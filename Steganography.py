import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image
import numpy as np

# -------------------- Embedding Function --------------------
def embed_text_in_image(image_path, text, output_path):
    img = Image.open(image_path).convert('RGB')
    data = np.array(img)
    flat_data = data.flatten()

    # Convert text to binary
    binary_text = ''.join(format(ord(c), '08b') for c in text)
    binary_text += '1111111111111110'  # Delimiter to mark end of message

    if len(binary_text) > len(flat_data):
        raise ValueError("Message too long to hide in this image!")

    # Embed bits safely in LSB
    for i in range(len(binary_text)):
        flat_data[i] = (flat_data[i] & 254) | int(binary_text[i])

    new_data = flat_data.reshape(data.shape)
    stego_img = Image.fromarray(new_data.astype('uint8'), 'RGB')
    stego_img.save(output_path)

# -------------------- Decoding Function --------------------
def decode_text_from_image(image_path):
    img = Image.open(image_path).convert('RGB')
    data = np.array(img)
    flat_data = data.flatten()

    binary_text = ""
    for value in flat_data:
        binary_text += str(value & 1)  # Extract LSB

    # Split by 8 bits and convert to characters
    chars = []
    for i in range(0, len(binary_text), 8):
        byte = binary_text[i:i+8]
        if byte == '11111111':  # Safety delimiter detection
            break
        if len(byte) < 8:
            continue
        char = chr(int(byte, 2))
        chars.append(char)
    return ''.join(chars)

# -------------------- GUI Functions --------------------
def load_image():
    path = filedialog.askopenfilename(filetypes=[("Image files", "*.png;*.jpg;*.jpeg")])
    if path:
        image_path.set(path)

def save_image():
    path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG files", "*.png")])
    if path:
        output_path.set(path)

def run_embedding():
    try:
        img_path = image_path.get()
        msg = message_entry.get("1.0", tk.END).strip()
        out_path = output_path.get()

        if not img_path or not msg or not out_path:
            messagebox.showwarning("Missing data", "Please select an image, enter text, and choose an output path.")
            return

        embed_text_in_image(img_path, msg, out_path)
        messagebox.showinfo("Success", f"Message embedded successfully!\nSaved as {out_path}")
    except Exception as e:
        messagebox.showerror("Error", str(e))

def run_decoding():
    try:
        img_path = filedialog.askopenfilename(filetypes=[("Image files", "*.png;*.jpg;*.jpeg")])
        if not img_path:
            return
        hidden_text = decode_text_from_image(img_path)
        if hidden_text:
            messagebox.showinfo("Decoded Message", hidden_text)
        else:
            messagebox.showinfo("Decoded Message", "No hidden message found.")
    except Exception as e:
        messagebox.showerror("Error", str(e))

# -------------------- GUI Setup --------------------
root = tk.Tk()
root.title("Binary Image Embedder & Decoder (Steganography)")
root.geometry("550x400")

image_path = tk.StringVar()
output_path = tk.StringVar()

tk.Label(root, text="1. Select Image to Embed Text:").pack()
tk.Entry(root, textvariable=image_path, width=60).pack()
tk.Button(root, text="Browse Image", command=load_image).pack(pady=5)

tk.Label(root, text="2. Enter Text to Embed:").pack()
message_entry = tk.Text(root, height=4, width=60)
message_entry.pack()

tk.Label(root, text="3. Output File Path:").pack()
tk.Entry(root, textvariable=output_path, width=60).pack()
tk.Button(root, text="Save As", command=save_image).pack(pady=5)

tk.Button(root, text="Embed Text", command=run_embedding, bg="lightblue").pack(pady=10)
tk.Button(root, text="Decode Text from Image", command=run_decoding, bg="lightgreen").pack(pady=10)

root.mainloop()
