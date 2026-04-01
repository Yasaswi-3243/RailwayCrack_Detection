import os
import uuid
import time
import base64
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from ultralytics import YOLO
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageEnhance, ImageFilter
import cv2
import numpy as np

# Setup Flask app
app = Flask(__name__, static_folder='frontend/dist', static_url_path='')
CORS(app)  # Enable CORS for all routes
app.secret_key = os.getenv("FLASK_SECRET_KEY", "rail_crack_secret")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Load YOLO model
MODEL_PATH = os.path.join(BASE_DIR, "best.pt")
model = YOLO(MODEL_PATH)  # Ensure best.pt is in the same directory
CLASS_NAMES = model.names

# Prediction function
def _predict_with_params(image_path, conf, iou, imgsz, augment=False, agnostic_nms=True):
    return model.predict(
        source=image_path,
        conf=conf,
        iou=iou,
        imgsz=imgsz,
        augment=augment,
        agnostic_nms=agnostic_nms,
        verbose=False,
    )

def _collect_boxes(result):
    if result.boxes is None or len(result.boxes) == 0:
        return np.empty((0, 4)), np.empty((0,)), np.empty((0,), dtype=int)
    return (
        result.boxes.xyxy.cpu().numpy(),
        result.boxes.conf.cpu().numpy(),
        result.boxes.cls.cpu().numpy().astype(int),
    )



def _enhancements(img: Image.Image):
    yield ("original", img)
    yield ("autocontrast", ImageOps.autocontrast(img))
    try:
        yield ("equalize", ImageOps.equalize(img))
    except Exception:
        pass
    yield ("sharp", ImageEnhance.Sharpness(img).enhance(1.8))
    yield ("contrast", ImageEnhance.Contrast(img).enhance(1.4))

def _variance_of_laplacian(arr: np.ndarray) -> float:
    """Measure blur; lower is blurrier."""
    return float(cv2.Laplacian(arr, cv2.CV_64F).var())

def _preprocess_for_blur(img: Image.Image) -> list[tuple[str, Image.Image]]:
    """Generate deblurred/denoised variants for tough images."""
    cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
    variants: list[tuple[str, Image.Image]] = []
    try:
        # Unsharp masking
        blur = cv2.GaussianBlur(cv, (0, 0), 2.0)
        usm = cv2.addWeighted(cv, 1.8, blur, -0.8, 0)
        variants.append(("usm", Image.fromarray(cv2.cvtColor(usm, cv2.COLOR_BGR2RGB))))
        # CLAHE on L channel
        lab = cv2.cvtColor(cv, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        lc = clahe.apply(l)
        clab = cv2.merge((lc, a, b))
        clahe_img = cv2.cvtColor(clab, cv2.COLOR_LAB2BGR)
        variants.append(("clahe", Image.fromarray(cv2.cvtColor(clahe_img, cv2.COLOR_BGR2RGB))))
        # Bilateral filter then sharpen
        bil = cv2.bilateralFilter(cv, d=7, sigmaColor=75, sigmaSpace=75)
        bil_sharp = cv2.addWeighted(bil, 1.5, cv, -0.5, 0)
        variants.append(("bil_sharp", Image.fromarray(cv2.cvtColor(bil_sharp, cv2.COLOR_BGR2RGB))))
    except Exception:
        pass
    return variants

def _is_crack_like(box, img: Image.Image) -> bool:
    """Heuristic to validate that a detection looks like a crack (not rust patch).
    Uses edge density and color to filter out false positives.
    """
    x1, y1, x2, y2 = [int(v) for v in box]
    x1 = max(0, x1); y1 = max(0, y1)
    x2 = min(img.size[0]-1, x2); y2 = min(img.size[1]-1, y2)
    if x2 <= x1 or y2 <= y1:
        return False
    roi = np.array(img.crop((x1, y1, x2, y2)))
    h, w = roi.shape[:2]
    # Aspect/Thinness
    thinness = min(h, w) / (max(h, w) + 1e-6)
    # Edge density
    gray = cv2.cvtColor(roi, cv2.COLOR_RGB2GRAY)
    edges = cv2.Canny(gray, 50, 150)
    edge_ratio = float((edges > 0).sum()) / (h * w)
    # Color (rust filter)
    hsv = cv2.cvtColor(roi, cv2.COLOR_RGB2HSV)
    mean_h = float(hsv[:, :, 0].mean()) * 2.0  # OpenCV 0-180 -> 0-360
    mean_s = float(hsv[:, :, 1].mean()) / 255.0
    # Heuristics:
    # - Crack should be relatively thin OR have high edge density
    # - Rust patches are reddish/orange with high saturation and low edge density
    crack_shape = thinness < 0.45 or edge_ratio > 0.08
    looks_like_rust = (5 <= mean_h <= 35) and (mean_s > 0.35) and (edge_ratio < 0.06)
    return crack_shape and not looks_like_rust



def _image_stats(img: Image.Image):
    g = img.convert("L")
    arr = np.array(g, dtype=np.float32)
    # entropy
    hist, _ = np.histogram(arr, bins=256, range=(0, 255), density=True)
    p = hist[hist > 0]
    entropy = float(-(p * np.log2(p)).sum())
    # edge strength via FIND_EDGES
    edges = g.filter(ImageFilter.FIND_EDGES)
    edge_mean = float(np.array(edges, dtype=np.float32).mean())
    # contrast (stddev)
    contrast = float(arr.std())
    return {"entropy": entropy, "edge_mean": edge_mean, "contrast": contrast}

def _auto_conf_schedule(img: Image.Image):
    s = _image_stats(img)
    # Heuristic: higher detail -> higher starting conf, else start lower
    if s["entropy"] > 6.0 or s["contrast"] > 55 or s["edge_mean"] > 20:
        base = [0.35, 0.28, 0.22, 0.18, 0.14, 0.10]
    else:
        base = [0.22, 0.18, 0.14, 0.10, 0.08, 0.05]
    return base

def _create_tiles(img: Image.Image, tile_size=640, overlap=0.25):
    """Split image into overlapping tiles for better small object detection"""
    w, h = img.size
    stride = int(tile_size * (1 - overlap))
    tiles = []
    
    for y in range(0, h, stride):
        for x in range(0, w, stride):
            x_end = min(x + tile_size, w)
            y_end = min(y + tile_size, h)
            x_start = max(0, x_end - tile_size) if x_end == w else x
            y_start = max(0, y_end - tile_size) if y_end == h else y
            
            tile = img.crop((x_start, y_start, x_end, y_end))
            tiles.append({
                'image': tile,
                'offset': (x_start, y_start),
                'box': (x_start, y_start, x_end, y_end)
            })
    return tiles

def _nms_merge(all_boxes, all_scores, all_labels, iou_threshold=0.5):
    """Merge overlapping detections from multiple passes using NMS"""
    if len(all_boxes) == 0:
        return np.empty((0, 4)), np.empty((0,)), np.empty((0,), dtype=int)
    
    boxes = np.array(all_boxes)
    scores = np.array(all_scores)
    labels = np.array(all_labels)
    
    # Simple NMS: keep highest score boxes, suppress overlapping ones
    keep = []
    order = scores.argsort()[::-1]
    
    while len(order) > 0:
        i = order[0]
        keep.append(i)
        
        if len(order) == 1:
            break
            
        # Compute IoU with remaining boxes
        xx1 = np.maximum(boxes[i, 0], boxes[order[1:], 0])
        yy1 = np.maximum(boxes[i, 1], boxes[order[1:], 1])
        xx2 = np.minimum(boxes[i, 2], boxes[order[1:], 2])
        yy2 = np.minimum(boxes[i, 3], boxes[order[1:], 3])
        
        w = np.maximum(0, xx2 - xx1)
        h = np.maximum(0, yy2 - yy1)
        inter = w * h
        
        area_i = (boxes[i, 2] - boxes[i, 0]) * (boxes[i, 3] - boxes[i, 1])
        area_rest = (boxes[order[1:], 2] - boxes[order[1:], 0]) * (boxes[order[1:], 3] - boxes[order[1:], 1])
        union = area_i + area_rest - inter
        
        iou = inter / (union + 1e-6)
        
        # Keep boxes with low IoU (not overlapping)
        inds = np.where(iou <= iou_threshold)[0]
        order = order[inds + 1]
    
    return boxes[keep], scores[keep], labels[keep]

def _merge_close_boxes(boxes, scores, labels, iou_thresh=0.2, dist_thresh=40):
    """Merge very close/overlapping boxes to reduce clutter."""
    if len(boxes) == 0:
        return boxes, scores, labels
    boxes = np.array(boxes)
    scores = np.array(scores)
    labels = np.array(labels)
    order = scores.argsort()[::-1]
    kept_boxes = []
    kept_scores = []
    kept_labels = []

    while len(order) > 0:
        i = order[0]
        box = boxes[i]
        score = scores[i]
        label = labels[i]

        xx1 = np.maximum(box[0], boxes[order[1:], 0])
        yy1 = np.maximum(box[1], boxes[order[1:], 1])
        xx2 = np.minimum(box[2], boxes[order[1:], 2])
        yy2 = np.minimum(box[3], boxes[order[1:], 3])

        w = np.maximum(0, xx2 - xx1)
        h = np.maximum(0, yy2 - yy1)
        inter = w * h
        area_i = (box[2]-box[0])*(box[3]-box[1])
        area_rest = (boxes[order[1:], 2]-boxes[order[1:], 0])*(boxes[order[1:], 3]-boxes[order[1:], 1])
        union = area_i + area_rest - inter + 1e-6
        iou = inter / union

        # center distance
        cx = (boxes[order[1:],0]+boxes[order[1:],2])/2 - (box[0]+box[2])/2
        cy = (boxes[order[1:],1]+boxes[order[1:],3])/2 - (box[1]+box[3])/2
        dist = np.sqrt(cx*cx + cy*cy)

        close = (iou > iou_thresh) | (dist < dist_thresh)
        merge_inds = np.where(close)[0]

        if len(merge_inds) > 0:
            idxs = order[1:][merge_inds]
            all_merge = np.concatenate(([i], idxs))
            merged_box = np.array([
                boxes[all_merge,0].min(),
                boxes[all_merge,1].min(),
                boxes[all_merge,2].max(),
                boxes[all_merge,3].max()
            ])
            merged_score = scores[all_merge].max()
            kept_boxes.append(merged_box)
            kept_scores.append(merged_score)
            kept_labels.append(label)  # keep main label
            # remove merged
            mask = np.ones(len(order), dtype=bool)
            mask[0] = False
            mask[1:][merge_inds] = False
            order = order[mask]
        else:
            kept_boxes.append(box)
            kept_scores.append(score)
            kept_labels.append(label)
            order = order[1:]

    return np.array(kept_boxes), np.array(kept_scores), np.array(kept_labels)



def _strip_tiles(img: Image.Image, strip_height=240, overlap=0.5, v_start=0.2, v_end=0.85):
    """Generate horizontal strip tiles across the likely rail web area."""
    w, h = img.size
    tiles = []
    y = int(h * v_start)
    end = int(h * v_end)
    stride = int(strip_height * (1 - overlap))
    if stride <= 0:
        stride = 1
    while y < end:
        y_end = min(y + strip_height, h)
        y_start = max(0, y_end - strip_height) if y_end == h else y
        tile = img.crop((0, y_start, w, y_end))
        tiles.append({'image': tile, 'offset': (0, y_start), 'box': (0, y_start, w, y_end)})
        if y_end == h:
            break
        y += stride
    return tiles

def _is_on_railway_track(box, image_size):
    """Check if detection is on the railway track metal/rail only (not ground/walls/platform).
    More permissive for long, thin horizontal cracks (longitudinal)."""
    x1, y1, x2, y2 = box
    img_w, img_h = image_size

    center_x = (x1 + x2) / 2
    center_y = (y1 + y2) / 2
    box_height = max(1.0, (y2 - y1))
    box_width = max(1.0, (x2 - x1))

    # Rail runs horizontally roughly across mid-height; widen band slightly
    vertical_on_track = (0.20 * img_h) < center_y < (0.70 * img_h)
    # Horizontal: allow near edges
    horizontal_on_track = (0.05 * img_w) < center_x < (0.95 * img_w)

    # Bounds checks against ballast/platform with a bit of tolerance
    if y2 > 0.75 * img_h:
        return False
    if y1 < 0.18 * img_h:
        return False

    box_width_ratio = box_width / img_w
    box_height_ratio = box_height / img_h
    elongation = max(box_width, box_height) / (min(box_width, box_height) + 1e-6)

    # Reject very tall boxes that span multiple regions
    if box_height_ratio > 0.40:
        return False

    # Reject extremely wide boxes unless they are very thin (likely a long crack)
    if box_width_ratio > 0.70:
        # Permit if long and thin (horizontal crack characteristic)
        if not (elongation >= 6.0 and (box_height / img_h) < 0.12):
            return False

    return horizontal_on_track and vertical_on_track

def _classify_crack_type(box, image_size, base_label):
    """Classify crack type based on orientation, position, and model label"""
    x1, y1, x2, y2 = box
    width = x2 - x1
    height = y2 - y1
    aspect_ratio = height / (width + 1e-6)
    img_w, img_h = image_size
    
    # If base label is specific, add orientation detail
    # Domain assumption: the rail runs horizontally in the image.
    # - Tall/narrow boxes -> vertical cracks across the rail -> Transverse
    # - Wide/short boxes -> along the rail -> Longitudinal
    if 'crack' in base_label.lower():
        if aspect_ratio >= 1.2:
            orient = 'Transverse'
        elif aspect_ratio <= 0.8:
            orient = 'Longitudinal'
        else:
            orient = 'Diagonal'
        return f"{base_label} ({orient})"
    
    # For other defect types, add position context
    if y1 < img_h * 0.3:
        position = "Head"
    elif y1 > img_h * 0.7:
        position = "Foot"
    else:
        position = "Web"
    
    return f"{base_label} ({position})"

def _assess_severity(box, confidence, image_size):
    """Assess crack severity based on size and confidence"""
    x1, y1, x2, y2 = box
    width = x2 - x1
    height = y2 - y1
    area = width * height
    img_w, img_h = image_size
    img_area = img_w * img_h
    
    # Calculate relative size
    relative_size = area / img_area
    length_mm = max(width, height)  # Approximate length in pixels (can be calibrated)
    
    # Severity assessment
    if confidence >= 0.6 and relative_size > 0.04:
        severity = "Critical"
        danger_level = "Immediate Action Required"
    elif confidence >= 0.35 and relative_size > 0.015:
        severity = "Moderate"
        danger_level = "Schedule Maintenance Soon"
    elif confidence >= 0.15 or relative_size > 0.008:
        severity = "Minor"
        danger_level = "Monitor Regularly"
    else:
        severity = "Minor"
        danger_level = "Routine Inspection"
    
    return {
        "severity": severity,
        "danger_level": danger_level,
        "length_px": int(max(width, height)),
        "width_px": int(min(width, height)),
        "area_px": int(area),
        "relative_size_pct": round(relative_size * 100, 2)
    }

def _is_crack_class(label_name):
    """Keep only actual crack detections - Cracks and Putus (rail break)"""
    label_str = str(label_name).lower()
    # Only accept Cracks and Putus (which means rail break/crack in Indonesian)
    return 'crack' in label_str or 'putus' in label_str

def detect_defects(image_path, conf: float | None = None, iou: float = 0.45, imgsz: int = 640):
    base_img = Image.open(image_path).convert("RGB")

    # Detect blur and prepare enhanced variants if needed
    base_arr = np.array(base_img.convert("L"))
    blur_score = _variance_of_laplacian(base_arr)
    is_blurry = blur_score < 120.0

    # Collect detections: direct + tiled (to catch thin/long cracks)
    all_boxes: list[list[float]] = []
    all_scores: list[float] = []
    all_labels: list[int] = []

    # 1) Direct full-image inference at higher resolution
    direct_conf = 0.01 if conf is None else conf  # Ultra-low threshold to catch even weak detections
    results = model.predict(source=image_path, conf=direct_conf, iou=iou, imgsz=max(1920, imgsz), augment=True, verbose=False)
    b, s, l = _collect_boxes(results[0])
    if len(s) > 0:
        all_boxes.extend(b.tolist())
        all_scores.extend([float(x) for x in s])
        all_labels.extend([int(x) for x in l])

    # 1b) If image is blurry, run predictions on deblurred variants
    if is_blurry:
        for name, var_img in _preprocess_for_blur(base_img):
            tmp = os.path.join(app.config['UPLOAD_FOLDER'], f"blur_{name}_{uuid.uuid4().hex[:6]}.jpg")
            var_img.save(tmp, format="JPEG", quality=95)
            try:
                r = model.predict(source=tmp, conf=max(0.008, direct_conf * 0.8), iou=iou, imgsz=max(1600, imgsz), augment=True, verbose=False)
                vb, vs, vl = _collect_boxes(r[0])
                if len(vs) > 0:
                    all_boxes.extend(vb.tolist())
                    all_scores.extend([float(x) * 0.98 for x in vs])
                    all_labels.extend([int(x) for x in vl])
            finally:
                try:
                    os.remove(tmp)
                except OSError:
                    pass

    # 2) Tiled inference for small/localized cracks - focused on rail web area
    tiles = _create_tiles(base_img, tile_size=512, overlap=0.5)
    tiles += _create_tiles(base_img, tile_size=640, overlap=0.4)
    tiles += _create_tiles(base_img, tile_size=800, overlap=0.3)
    # Add horizontal strips specifically targeting rail web area (middle 60% of image)
    tiles += _strip_tiles(base_img, strip_height=280, overlap=0.5, v_start=0.25, v_end=0.8)
    temp_files = []
    try:
        for t in tiles:
            tmp_path = os.path.join(app.config['UPLOAD_FOLDER'], f"tmp_{uuid.uuid4().hex[:8]}.jpg")
            t['image'].save(tmp_path, format="JPEG", quality=95)
            temp_files.append(tmp_path)
            tile_conf = max(0.02, direct_conf * 0.5)  # Very sensitive for catching cracks
            r = model.predict(source=tmp_path, conf=tile_conf, iou=iou, imgsz=640, augment=True, verbose=False)
            tb, ts, tl = _collect_boxes(r[0])
            if len(ts) > 0:
                # Offset back to full-image coordinates
                ox, oy = t['offset']
                tb[:, [0, 2]] += ox
                tb[:, [1, 3]] += oy
                all_boxes.extend(tb.tolist())
                all_scores.extend([float(x) for x in ts])
                all_labels.extend([int(x) for x in tl])
            
            # Also try enhanced version for subtle cracks
            try:
                enhanced_tile = ImageEnhance.Contrast(t['image']).enhance(1.8)
                enhanced_tile = ImageEnhance.Sharpness(enhanced_tile).enhance(1.6)
                enh_path = os.path.join(app.config['UPLOAD_FOLDER'], f"enh_{uuid.uuid4().hex[:8]}.jpg")
                enhanced_tile.save(enh_path, format="JPEG", quality=95)
                temp_files.append(enh_path)
                enh_conf = max(0.01, direct_conf * 0.4)
                er = model.predict(source=enh_path, conf=enh_conf, iou=iou, imgsz=640, augment=False, verbose=False)
                etb, ets, etl = _collect_boxes(er[0])
                if len(ets) > 0:
                    ox, oy = t['offset']
                    etb[:, [0, 2]] += ox
                    etb[:, [1, 3]] += oy
                    all_boxes.extend(etb.tolist())
                    all_scores.extend([float(x) * 0.95 for x in ets])  # Slightly discount enhanced detections
                    all_labels.extend([int(x) for x in etl])
            except:
                pass
    finally:
        for p in temp_files:
            try:
                os.remove(p)
            except OSError:
                pass

    # Merge with NMS then merge-close to reduce clutter
    if len(all_boxes) > 0:
        # Separate cracks from other defects for better filtering
        crack_indices = []
        other_indices = []
        
        for i, label_idx in enumerate(all_labels):
            label_name = CLASS_NAMES[label_idx].lower() if label_idx < len(CLASS_NAMES) else ""
            if 'crack' in label_name:
                crack_indices.append(i)
            else:
                other_indices.append(i)
        
        # Filter out very small detections and non-track detections
        img_area = base_img.size[0] * base_img.size[1]
        img_size = (base_img.size[0], base_img.size[1])
        valid_indices = []
        
        for i, box in enumerate(all_boxes):
            width = box[2] - box[0]
            height = box[3] - box[1]
            box_area = width * height
            
            # CRITICAL: Only keep detections on railway track area
            if not _is_on_railway_track(box, img_size):
                continue
            
            # Keep cracks with lower size threshold, others need to be larger
            if i in crack_indices:
                # Keep cracks with very low threshold - even tiny ones can be significant
                crack_like = _is_crack_like(box, base_img)
                if ((box_area / img_area) > 0.00005 or all_scores[i] > 0.08) and crack_like:
                    valid_indices.append(i)
            else:
                # Other defects need larger size or higher confidence
                if (box_area / img_area) > 0.0008 or all_scores[i] > 0.5:
                    valid_indices.append(i)
        
        if len(valid_indices) > 0:
            all_boxes = [all_boxes[i] for i in valid_indices]
            all_scores = [all_scores[i] for i in valid_indices]
            all_labels = [all_labels[i] for i in valid_indices]
            
            nms_boxes, nms_scores, nms_labels = _nms_merge(all_boxes, all_scores, all_labels, iou_threshold=0.35)
            final_boxes, final_scores, final_labels = _merge_close_boxes(nms_boxes, nms_scores, nms_labels, iou_thresh=0.2, dist_thresh=40)
            
            # Prioritize cracks: separate cracks from other detections
            crack_mask = []
            for i, label_idx in enumerate(final_labels):
                label_name = CLASS_NAMES[int(label_idx)].lower() if int(label_idx) < len(CLASS_NAMES) else ""
                crack_mask.append('crack' in label_name)
            
            crack_mask = np.array(crack_mask)
            crack_boxes = final_boxes[crack_mask]
            crack_scores = final_scores[crack_mask]
            crack_labels = final_labels[crack_mask]
            
            other_boxes = final_boxes[~crack_mask]
            other_scores = final_scores[~crack_mask]
            other_labels = final_labels[~crack_mask]
            
            # Keep top 15 cracks and top 3 other defects
            if len(crack_scores) > 15:
                order = crack_scores.argsort()[::-1][:15]
                crack_boxes = crack_boxes[order]
                crack_scores = crack_scores[order]
                crack_labels = crack_labels[order]
            
            if len(other_scores) > 3:
                order = other_scores.argsort()[::-1][:3]
                other_boxes = other_boxes[order]
                other_scores = other_scores[order]
                other_labels = other_labels[order]
            
            # Combine cracks first, then others
            if len(crack_scores) > 0 and len(other_scores) > 0:
                final_boxes = np.vstack([crack_boxes, other_boxes])
                final_scores = np.concatenate([crack_scores, other_scores])
                final_labels = np.concatenate([crack_labels, other_labels])
            elif len(crack_scores) > 0:
                final_boxes = crack_boxes
                final_scores = crack_scores
                final_labels = crack_labels
            elif len(other_scores) > 0:
                final_boxes = other_boxes
                final_scores = other_scores
                final_labels = other_labels
            else:
                final_boxes = np.empty((0,4))
                final_scores = np.empty((0,))
                final_labels = np.empty((0,), dtype=int)
        else:
            final_boxes = np.empty((0,4))
            final_scores = np.empty((0,))
            final_labels = np.empty((0,), dtype=int)
    else:
        final_boxes = np.empty((0,4))
        final_scores = np.empty((0,))
        final_labels = np.empty((0,), dtype=int)

    # Draw and export
    image = base_img.copy()
    boxes = final_boxes
    scores = final_scores
    labels = final_labels

    draw = ImageDraw.Draw(image)
    try:
        font = ImageFont.truetype("arial.ttf", size=max(12, image.size[0] // 60))
    except Exception:
        font = ImageFont.load_default()

    box_thickness = max(3, min(image.size) // 150)
    detections = []
    box_number = 0
    
    for box, label, score in zip(boxes, labels, scores):
        x_min, y_min, x_max, y_max = box
        label_name = CLASS_NAMES.get(label, str(label)) if isinstance(CLASS_NAMES, dict) else CLASS_NAMES[label]
        
        # Filter: only keep crack-related detections
        if not _is_crack_class(label_name):
            continue
        
        box_number += 1
        
        # Classify crack type and assess severity
        crack_type = _classify_crack_type(box, image.size, label_name)
        severity_info = _assess_severity(box, score, image.size)
        
        # Color code by severity
        if severity_info["severity"] == "Critical":
            color = "#ff0000"  # Red
        elif severity_info["severity"] == "Moderate":
            color = "#ff8c00"  # Orange
        else:
            color = "#ffff00"  # Yellow
        
        # Draw bounding box
        draw.rectangle([x_min, y_min, x_max, y_max], outline=color, width=box_thickness)
        
        # Label with box number, crack type and confidence
        text = f"Box {box_number}: {crack_type} ({score*100:.1f}%)"
        
        try:
            tw, th = draw.textbbox((0, 0), text, font=font)[2:]
        except Exception:
            tw, th = len(text) * 7, font.size + 4
        
        pad = 4
        text_bg_y = max(0, y_min - th - 2 * pad)
        text_bg = [x_min, text_bg_y, x_min + tw + 2 * pad, y_min]
        draw.rectangle(text_bg, fill=color)
        draw.text((x_min + pad, text_bg_y + pad), text, fill="black", font=font)
        
        # Store detailed detection info (convert all numpy types to Python native)
        detections.append({
            "box_number": box_number,
            "label": str(label_name),
            "crack_type": str(crack_type),
            "severity": str(severity_info["severity"]),
            "danger_level": str(severity_info["danger_level"]),
            "confidence": float(score),
            "length_px": int(severity_info["length_px"]),
            "width_px": int(severity_info["width_px"]),
            "area_px": int(severity_info["area_px"]),
            "relative_size": float(severity_info["relative_size_pct"]),
            "box": [float(x_min), float(y_min), float(x_max), float(y_max)],
            "color": color
        })

    output_name = f"output_{uuid.uuid4().hex[:8]}.png"
    output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_name)
    image.save(output_path)
    return output_name, detections

# API endpoint for React frontend
@app.route("/api/predict", methods=["POST"])
def api_predict():
    """API endpoint for React frontend - returns JSON"""
    try:
        if 'image' not in request.files:
            return jsonify({"error": "No image provided"}), 400
        
        file = request.files['image']
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        
        # Save image temporarily
        filename = uuid.uuid4().hex + os.path.splitext(file.filename)[1]
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(image_path)
        
        # Run detection
        start_time = time.time()
        output_name, detections = detect_defects(image_path, conf=None)
        analysis_time = f"{time.time() - start_time:.2f}s"
        
        # Read the output image and convert to base64
        output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_name) if output_name else None
        image_base64 = None
        if output_path and os.path.exists(output_path):
            with open(output_path, 'rb') as img_file:
                image_base64 = base64.b64encode(img_file.read()).decode('utf-8')
        
        # Format detections for frontend
        formatted_detections = []
        if detections:
            for det in detections:
                formatted_detections.append({
                    'class': det.get('class', 'Crack'),
                    'confidence': float(det.get('confidence', 0)),
                    'x': float(det.get('x', 0)),
                    'y': float(det.get('y', 0)),
                    'width': float(det.get('width', 0)),
                    'height': float(det.get('height', 0)),
                })
        
        return jsonify({
            "success": True,
            "image": image_base64,
            "detections": formatted_detections,
            "analysis_time": analysis_time,
            "total_detections": len(formatted_detections)
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_react(path):
    # Keep API routes handled by dedicated endpoints.
    if path.startswith("api/"):
        return jsonify({"error": "Not found"}), 404

    static_dir = app.static_folder
    if path and os.path.exists(os.path.join(static_dir, path)):
        return send_from_directory(static_dir, path)
    return send_from_directory(static_dir, "index.html")

# Start the server
if __name__ == "__main__":
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    port = int(os.getenv("PORT", "5001"))
    app.run(debug=True, host='0.0.0.0', port=port)
