import tkinter as tk
from tkinter import messagebox, ttk
from tkinter import filedialog
from PIL import Image, ImageTk
import json
import os

class DataLabelingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Data Labeling App")

        # Add padding to the main window
        self.root.geometry("+" + str(20) + "+" + str(20))  # Set the window position
        self.root.configure(padx=20, pady=20)

        # ------------ Initialize global state ------------ #

        # Label variables
        self.image_path = ""
        self.classes = []
        self.bboxes = []
        self.class_bbox_mapping = {}
        self.class_and_bboxes_mapping = {}

        # From dropdown...
        self.class_names = self.read_class_names_from_txt()

        # List of images in dir
        self.image_index = 0
        self.image_list = []

        # Bbox start conditions
        self.start_x = 0
        self.start_y = 0

        # List to store annotations for all images
        self.output_data = []

        # ----------------- GUI stuff --------------------- #\

        # Create UI elements
        self.upload_button = tk.Button(root, text="Choose Your Folder", command=self.upload_image)
        self.upload_button.grid(row=0, column=0, sticky="w")

        # Create a fixed Txt Label to display the image directory path
        self.image_dir_label = tk.Label(root, text="Image Directory: ")
        self.image_dir_label.grid(row=0, column=1, sticky="w", pady=5)

        # Create a StringVar to update the label dynamically
        self.image_dir_path_var = tk.StringVar()
        self.image_dir_path_label = tk.Label(root, textvariable=self.image_dir_path_var, wraplength=300)
        self.image_dir_path_label.grid(row=0, column=2, columnspan=2, sticky="w", pady=5)

        # Init "Image Canvas" button
        self.canvas = tk.Canvas(root)
        self.canvas.grid(row=1, column=0, rowspan=6, padx=10)

        # Bind the <Left Mouse Button> event to the save_data method
        self.canvas.bind("<ButtonRelease-1>")

        # Init "Image Counter" plain text
        self.image_count_label = tk.Label(root, text="")
        self.image_count_label.grid(row=7, column=0, sticky="w", pady=5)

        # Init "Coordinates" plain text
        self.image_count_label = tk.Label(root, text=f"Coordinates: {self.start_x}, {self.start_y}, {self.start_x + self.canvas.winfo_width()}, {self.start_y + self.canvas.winfo_height()}")
        self.image_count_label.grid(row=7, column=1, sticky="w", pady=5)

        # Init "Previous" button
        self.prev_button = tk.Button(root, text="<- Previous", command=self.prev_image)
        self.prev_button.grid(row=8, column=0, sticky="w", pady=5)

        # Init "Next" button
        self.next_button = tk.Button(root, text="Next ->", command=self.next_image)
        self.next_button.grid(row=8, column=1, sticky="w", pady=5)

        # Init "Refresh" button
        self.refresh_button = tk.Button(root, text="Refresh", command=self.refresh_data)
        self.refresh_button.grid(row=8, column=2, sticky="w", pady=5)

        # Init "Save" button
        self.save_button = tk.Button(root, text="Save", command=self.save_data)
        self.save_button.grid(row=8, column=3, sticky="w", pady=5)

        # Init "Drowdown" Menu
        self.selected_class = tk.StringVar()
        self.class_dropdown = ttk.Combobox(root, textvariable=self.selected_class, values=self.class_names)
        self.class_dropdown.grid(row=9, column=0, sticky="w", pady=5)

        # Init "Textbox Widget" to display bounding box coordinates
        self.bbox_text = tk.Text(root, height=30, width=30)
        self.bbox_text.grid(row=1, column=2, rowspan=6, sticky="w", padx=10)
        self.bbox_text.insert(tk.END, "Bounding Box Coordinates:\n")

        # -------------- On-Start Actions ----------------- #

        # Load existing bounding box coordinates from output.json on startup
        self.load_existing_bounding_boxes()

    def upload_image(self):
        directory_path = filedialog.askdirectory()
        if directory_path:
            self.image_list = [os.path.join(directory_path, file) for file in os.listdir(directory_path) if file.lower().endswith(('.png', '.jpg', '.jpeg'))]

            if self.image_list:
                # Load the first image
                self.image_path = self.image_list[self.image_index]

                # Load existing bounding box coordinates for the selected image
                self.load_existing_bounding_boxes()

                self.load_image()
                self.update_navigation_elements()

                # Bind mouse events for drawing bounding box
                self.canvas.bind("<Button-1>", self.start_bbox)
                self.canvas.bind("<B1-Motion>", self.draw_bbox)
                self.load_existing_bounding_boxes()

                # Update the image directory path label
                self.image_dir_path_var.set(directory_path)

    def read_class_names_from_txt(self):
        class_names = []
        try:
            with open('class_list.txt', 'r') as file:
                class_names = [line.strip() for line in file.readlines()]
        except FileNotFoundError:
            print("class_list.txt not found. Please create the file with one class per line.")
        return class_names

    def load_existing_bounding_boxes(self):
        """ Helper function to load in existing annotations on startup """
        output_json_path = "output.json"
        if os.path.exists(output_json_path):
            with open(output_json_path, "r") as json_file:
                self.output_data = json.load(json_file)

            # Find current image entry in output_data
            current_image_data = next((item for item in self.output_data if item["image"] == self.image_path), None)

            # Display existing bounding box coordinates in the Text widget
            self.display_bounding_boxes(current_image_data)

    # def load_existing_bounding_boxes(self):
    #     """ Helper function to load in existing annotations """
    #     # Load existing bounding box coordinates from output.json for the selected image
    #     output_json_path = "output.json"
    #     if os.path.exists(output_json_path):
    #         with open(output_json_path, "r") as json_file:
    #             self.output_data = json.load(json_file)

    #         existing_image_data = next((item for item in self.output_data if item["image"] == self.image_path), None)

    #         if existing_image_data:
    #             # Display existing bounding box coordinates in the Text widget
    #             self.display_bounding_boxes(existing_image_data)

    def prev_image(self):
        if self.image_index > 0:
            # Save data for the current image before moving to the previous one
            # self.save_data()

            # Load the previous image
            self.image_index -= 1
            self.image_path = self.image_list[self.image_index]
            self.load_image()
            self.update_navigation_elements()
            self.load_existing_bounding_boxes()  # Load existing bounding box coordinates for the selected image

    def next_image(self):
        if self.image_index < len(self.image_list) - 1:
            # Save data for the current image before moving to the next one
            # self.save_data()

            # Load the next image
            self.image_index += 1
            self.image_path = self.image_list[self.image_index]
            self.load_image()
            self.update_navigation_elements()
            self.load_existing_bounding_boxes()  # Load existing bounding box coordinates for the selected image

    def update_navigation_elements(self):
        # Update the text showing image count
        current_count = self.image_index + 1
        total_count = len(self.image_list)
        self.image_count_label.config(text=f"{current_count} of {total_count}")

        # Disable/enable Previous and Next buttons based on the current image index
        self.prev_button["state"] = tk.NORMAL if self.image_index > 0 else tk.DISABLED
        self.next_button["state"] = tk.NORMAL if self.image_index < len(self.image_list) - 1 else tk.DISABLED

        # Clear the bounding box coordinates text only if "Save" button is not clicked
        if not self.classes or not self.bboxes:
            self.bbox_text.delete("1.0", tk.END)
            self.bbox_text.insert(tk.END, "Bounding Box Coordinates:\n")

    # def update_navigation_elements(self):
    #     # Update the text showing image count
    #     current_count = self.image_index + 1
    #     total_count = len(self.image_list)
    #     self.image_count_label.config(text=f"{current_count} of {total_count}")

    #     # Disable/enable Previous and Next buttons based on the current image index
    #     self.prev_button["state"] = tk.NORMAL if self.image_index > 0 else tk.DISABLED
    #     self.next_button["state"] = tk.NORMAL if self.image_index < len(self.image_list) - 1 else tk.DISABLED

    #     # Clear the bounding box coordinates text
    #     self.bbox_text.delete("1.0", tk.END)
    #     self.bbox_text.insert(tk.END, "Bounding Box Coordinates:\n")

    def load_image(self):
        if self.image_path:
            # Open the image using PIL
            pil_image = Image.open(self.image_path)

            # Convert PIL image to Tkinter PhotoImage
            tk_image = ImageTk.PhotoImage(pil_image)

            self.canvas.config(width=tk_image.width(), height=tk_image.height())
            self.canvas.create_image(0, 0, anchor=tk.NW, image=tk_image)
            self.canvas.image = tk_image

    def start_bbox(self, event):
        self.start_x = self.canvas.canvasx(event.x)
        self.start_y = self.canvas.canvasy(event.y)

    def draw_bbox(self, event):
        current_x = self.canvas.canvasx(event.x)
        current_y = self.canvas.canvasy(event.y)

        # Remove previous bbox rectangle
        self.canvas.delete("bbox")

        # Draw the new bbox rectangle
        self.canvas.create_rectangle(
            self.start_x, self.start_y, current_x, current_y,
            outline="red", width=2, tags="bbox"
        )

        # Update the end coordinates
        self.end_x = current_x
        self.end_y = current_y

    def refresh_data(self):
        # Refresh the bounding box coordinates text by loading existing bounding boxes
        self.load_existing_bounding_boxes()

    def save_data(self):
        if self.image_path:
            class_name = self.selected_class.get()
            # bbox_coords = (self.start_x, self.start_y, self.start_x + self.canvas.winfo_width(), self.start_y + self.canvas.winfo_height())

            # Convert coords to COCO format!!
            x_min = min(self.start_x, self.end_x)
            y_min = min(self.start_y, self.end_y)
            box_width = abs(self.end_x - self.start_x)
            box_height = abs(self.end_y - self.start_y)

            # bbox_coords = (self.start_x, self.start_y, self.end_x, self.end_y)  # Use the end coordinates
            bbox_coords = (x_min, y_min, box_width, box_height)

            # Update data for the current class
            if class_name not in self.class_and_bboxes_mapping:
                self.class_and_bboxes_mapping[class_name] = []

            # Append the bounding box coordinates for the current class
            self.class_and_bboxes_mapping[class_name].append(bbox_coords)

            # Clear the bounding box coordinates text
            self.bbox_text.delete("1.0", tk.END)
            self.bbox_text.insert(tk.END, "Bounding Box Coordinates:\n")

            # Check if entry for current image already exists in output_data
            current_image_data = next((item for item in self.output_data if item["image"] == self.image_path), None)

            if current_image_data:
                # Update existing entry
                current_image_data.setdefault("class_and_bboxes", []).extend({"class": key, "bboxes": value} for key, value in self.class_and_bboxes_mapping.items())
                print("Appended")
            else:
                # Create a new entry
                current_image_data = {"image": self.image_path, "class_and_bboxes": [{"class": key, "bboxes": value} for key, value in self.class_and_bboxes_mapping.items()]}
                self.output_data.append(current_image_data)
                print("Created new var")

            # Clear the temporary list variable and the coordinates
            self.class_and_bboxes_mapping.clear()

            # Save data to JSON file
            with open("output.json", "w") as json_file:
                json.dump(self.output_data, json_file)

            # Display bounding box coordinates in the Text widget
            self.display_bounding_boxes(current_image_data)

    def display_bounding_boxes(self, image_data=None):
        """Bounding coord widget display"""
        # Clear the bounding box coordinates text
        self.bbox_text.delete("1.0", tk.END)
        self.bbox_text.insert(tk.END, "Bounding Box Coordinates:\n")

        # Display bounding box coordinates organized by class
        if image_data and "class_and_bboxes" in image_data:
            for class_info in image_data['class_and_bboxes']:
                class_name = class_info["class"]
                for bbox in class_info['bboxes']:
                    # Draw write bbox coords to the widget
                    self.bbox_text.insert(tk.END, f"{class_name}: {bbox}\n")

                    # Draw rectangles on the canvas
                    # x1, y1, x2, y2 = bbox
                    # self.canvas.create_rectangle(x1, y1, x2, y2, outline='blue')
                    x, y, w, h = bbox
                    self.canvas.create_rectangle(x, y, x+w, y+h, outline='blue')

                    # Display class label above the bounding box
                    class_label_x = (x + x + w) / 2  # Calculate the x-coordinate for class label
                    class_label_y = y - 10  # Adjust this value based on your preference for the y-coordinate
                    self.canvas.create_text(class_label_x, class_label_y, text=class_name, fill='blue')

        else:
            # Display a placeholder message if no bounding box coordinates are found
            self.bbox_text.insert(tk.END, "No existing bounding box coordinates for this image.\n")

    # def display_bounding_boxes(self, image_data=None):
    #     """Bounding coord widgert display"""
    #     # Clear the bounding box coordinates text
    #     self.bbox_text.delete("1.0", tk.END)
    #     self.bbox_text.insert(tk.END, "Bounding Box Coordinates:\n")

    #     # Display bounding box coordinates organized by class
    #     if image_data:
    #         self.bbox_text.insert(tk.END, f"\n{os.path.basename(image_data['image'])}:\n")
    #         for class_name, bbox in zip(image_data['classes'], image_data['bboxes']):
    #             self.bbox_text.insert(tk.END, f"{class_name}: {bbox}\n")
    #     else:
    #         # Display a placeholder message if no bounding box coordinates are found
    #         self.bbox_text.insert(tk.END, "No existing bounding box coordinates for this image.\n")


if __name__ == "__main__":
    root = tk.Tk()
    app = DataLabelingApp(root)
    root.mainloop()
