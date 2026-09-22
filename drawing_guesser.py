import tkinter as tk
from tkinter import colorchooser
from PIL import Image, ImageDraw, ImageOps, ImageFilter
import io
import ssl

# Workaround for SSL certificate verification failure on macOS/some environments
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

MODEL_ERROR = None
try:
    import tensorflow as tf
    import numpy as np
    model = tf.keras.applications.MobileNetV2(weights='imagenet')
    from tensorflow.keras.applications.mobilenet_v2 import preprocess_input, decode_predictions
    HAS_TF = True
except ImportError:
    HAS_TF = False
    MODEL_ERROR = "TensorFlow not installed."
except Exception as e:
    HAS_TF = False
    MODEL_ERROR = f"Error loading model: {e}"
    print(f"Error loading model: {e}")

class DrawingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("AI Drawing Guesser")

        self.brush_size = 5
        self.brush_color = "black"
        self.bg_color = "white"

        # Image for PIL to draw on (which we pass to the model)
        self.canvas_width = 800
        self.canvas_height = 600
        self.image = Image.new("RGB", (self.canvas_width, self.canvas_height), self.bg_color)
        self.draw = ImageDraw.Draw(self.image)

        self.old_x = None
        self.old_y = None

        self.setup_ui()

    def setup_ui(self):
        # Top Toolbar
        self.toolbar = tk.Frame(self.root, bg="lightgray", pady=5)
        self.toolbar.pack(side="top", fill="x")

        # Functionality 1: Pencil
        self.btn_pencil = tk.Button(self.toolbar, text="Pencil", command=self.use_pencil)
        self.btn_pencil.pack(side="left", padx=5)

        # Functionality 2: Eraser
        self.btn_eraser = tk.Button(self.toolbar, text="Eraser", command=self.use_eraser)
        self.btn_eraser.pack(side="left", padx=5)

        # Functionality 3: Color Chooser
        self.btn_color = tk.Button(self.toolbar, text="Choose Color", command=self.choose_color)
        self.btn_color.pack(side="left", padx=5)

        # Functionality 4: Change Brush Size
        self.size_scale = tk.Scale(self.toolbar, from_=1, to=50, orient="horizontal", label="Brush Size")
        self.size_scale.set(self.brush_size)
        self.size_scale.pack(side="left", padx=5)

        # Functionality 5: Clear Canvas
        self.btn_clear = tk.Button(self.toolbar, text="Clear Canvas", command=self.clear_canvas)
        self.btn_clear.pack(side="left", padx=5)

        # Label to display the prediction
        self.guess_label = tk.Label(self.toolbar, text="Draw something to get a real-time guess!", bg="lightgray", font=("Arial", 12))
        self.guess_label.pack(side="left", padx=20)

        # Canvas
        self.canvas = tk.Canvas(self.root, width=self.canvas_width, height=self.canvas_height, bg="white", cursor="cross")
        self.canvas.pack(fill="both", expand=True)

        # Bindings for drawing
        self.canvas.bind("<B1-Motion>", self.paint)
        self.canvas.bind("<ButtonRelease-1>", self.reset)

        # Start the periodic real-time guess loop
        self.root.after(1000, self.periodic_guess)
    def use_pencil(self):
        self.brush_color = "black"

    def use_eraser(self):
        self.brush_color = "white"

    def choose_color(self):
        color = colorchooser.askcolor(color=self.brush_color)[1]
        if color:
            self.brush_color = color

    def clear_canvas(self):
        self.canvas.delete("all")
        self.image = Image.new("RGB", (self.canvas_width, self.canvas_height), self.bg_color)
        self.draw = ImageDraw.Draw(self.image)
        self.guess_label.config(text="Draw something to get a real-time guess!")

    def paint(self, event):
        self.brush_size = self.size_scale.get()
        if self.old_x and self.old_y:
            # Draw on Tkinter canvas
            self.canvas.create_line(self.old_x, self.old_y, event.x, event.y,
                                    width=self.brush_size, fill=self.brush_color,
                                    capstyle=tk.ROUND, smooth=tk.TRUE, splinesteps=36)
            # Draw on PIL image for model prediction
            self.draw.line([self.old_x, self.old_y, event.x, event.y],
                           fill=self.brush_color, width=self.brush_size)

        self.old_x = event.x
        self.old_y = event.y

    def reset(self, event):
        self.old_x = None
        self.old_y = None

    def periodic_guess(self):
        self.guess_drawing()
        # Schedule the next guess in 1000 milliseconds
        self.root.after(1000, self.periodic_guess)

    def guess_drawing(self):
        if not HAS_TF:
            self.guess_label.config(text=f"Cannot guess. {MODEL_ERROR}")
            return

        try:
            img = self.image

            # Get bounding box of non-white pixels
            gray = img.convert("L")
            inv = Image.eval(gray, lambda x: 255 - x)
            bbox = inv.getbbox()

            if bbox:
                # Add padding to bounding box
                margin = 40
                w, h = img.size
                bbox = (
                    max(0, bbox[0] - margin),
                    max(0, bbox[1] - margin),
                    min(w, bbox[2] + margin),
                    min(h, bbox[3] + margin)
                )

                cropped = img.crop(bbox)

                # Pad to square
                cw, ch = cropped.size
                size = max(cw, ch)

                square_img = Image.new("RGB", (size, size), self.bg_color)
                square_img.paste(cropped, ((size - cw) // 2, (size - ch) // 2))
                img = square_img

            # Invert the image (white lines on black background works better for some ImageNet models)
            img = ImageOps.invert(img)

            # Apply slight blur to thicken lines
            img = img.filter(ImageFilter.GaussianBlur(1))

            # Resize image to 224x224 as required by MobileNetV2 with LANCZOS for better downsampling
            img = img.resize((224, 224), Image.Resampling.LANCZOS)
            img_array = tf.keras.preprocessing.image.img_to_array(img)
            img_array = np.expand_dims(img_array, axis=0)
            img_array = preprocess_input(img_array)

            # Predict
            predictions = model.predict(img_array)
            decoded_predictions = decode_predictions(predictions, top=3)[0]

            # Get best prediction
            top_guess = decoded_predictions[0][1]
            confidence = decoded_predictions[0][2]

            guess_text = f"I guess: {top_guess.replace('_', ' ').capitalize()} ({confidence:.1%})"
            self.guess_label.config(text=guess_text)

        except Exception as e:
            self.guess_label.config(text=f"Error analyzing image.")
            print(f"Error: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = DrawingApp(root)
    root.mainloop()
