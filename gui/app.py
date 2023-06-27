import tkinter as tk
from tkinter import filedialog

def open_file():
    global project_name
    file_path = filedialog.askopenfilename()
    if file_path:
        with open(file_path, 'r') as file:
            project_name.set(file.readline().strip())
            for line in file:
                rect_data = line.strip().split()
                rect_name, width, height = rect_data[:3]
                width, height = int(width), int(height)
                coords = [(int(x), int(y)) for x, y in zip(rect_data[3::2], rect_data[4::2])]
                create_rectangle(rect_name, width, height, coords)

def save_file():
    global canvas
    file_path = filedialog.asksaveasfilename()
    if file_path:
        with open(file_path, 'w') as file:
            file.write(f"{project_name.get()}\n")
            for item in canvas.find_withtag("rectangle"):
                name = canvas.itemcget(item, "tags").split()[1]
                x1, y1, x2, y2 = canvas.coords(item)
                file.write(f"{name} {x1} {y1} {x2} {y2}\n")

def create_rectangle(rect_name, origin_width, origin_height, coords):
    global canvas,obj_grp
    mesh_size = 20
    width = origin_width * mesh_size
    height = origin_height * mesh_size
    x, y = 10 + mesh_size/2, 10 + mesh_size/2
    rect = canvas.create_rectangle(x, y, x + width, y + height, fill="#7FB069", tags=(f"rectangle {rect_name}"))
    draw_mesh()
    name_text = canvas.create_text(x + width / 2, y + height / 2, text=rect_name, tags=(f"name {rect_name}"))
    canvas.tag_bind(rect, "<ButtonPress-1>", on_rectangle_press)
    canvas.tag_bind(rect, "<B1-Motion>", on_rectangle_move)

    obj_grp.append([rect,name_text])

    # Display coordinates within the rectangle
    for i, (coord_x, coord_y) in enumerate(coords, start=1):
        coord_x, coord_y = x + coord_x * mesh_size + mesh_size/2, y + coord_y * mesh_size + mesh_size/2
        coord_text = canvas.create_text(coord_x, coord_y, text=f"P{i}", tags=(f"coord {rect_name}"))
        obj_grp[-1].append(coord_text)

    # Update the rectangle information in the left area
    update_rectangle_info(rect_name, origin_width, origin_height)
    

def update_rectangle_info(rect_name, width, height):
    label = tk.Label(rectangle_info_frame, text=f"{rect_name}: {width}x{height}", bg="#2C2C2C", fg="white")
    label.pack(side=tk.TOP, anchor="w", padx=10, pady=5)

def draw_mesh():
    global canvas
    mesh_size = 20
    for i in range(0, 2000, mesh_size):
        canvas.create_line(i, 0, i, 2000, fill="#C0C0C0")
    for i in range(0, 2000, mesh_size):
        canvas.create_line(0, i, 2000, i, fill="#C0C0C0")

def on_rectangle_press(event):
    global prev_x, prev_y
    global figure
    prev_x, prev_y = event.x, event.y
    figure = canvas.find_closest(event.x, event.y)

def on_rectangle_move(event):
    global canvas, prev_x, prev_y, obj_grp, figure
    mesh_size = 20
    dx, dy = event.x - prev_x, event.y - prev_y
    dx = round(dx / mesh_size) * mesh_size
    dy = round(dy / mesh_size) * mesh_size
    item = figure
    canvas.move(item, dx, dy)
    for contents in obj_grp:
        if item[0] in contents:
            for v in contents:
                if v == item[0]:
                    continue
                canvas.move(v,dx,dy)

    prev_x, prev_y = event.x, event.y

app = tk.Tk()
app.title("Rectangle Mover with Mesh and Labels")
app.geometry("1000x600")

menubar = tk.Menu(app)
app.config(menu=menubar)

filemenu = tk.Menu(menubar)
menubar.add_cascade(label="File", menu=filemenu)
filemenu.add_command(label="Open", command=open_file)
filemenu.add_command(label="Save", command=save_file)
filemenu.add_separator()
filemenu.add_command(label="Exit", command=app.quit)

# Left area for project name and rectangle info
left_frame = tk.Frame(app, width=200, bg="#2C2C2C")
left_frame.pack(side=tk.LEFT, fill=tk.Y)

project_name = tk.StringVar()
project_name.set("No project loaded")
project_name_label = tk.Label(left_frame, textvariable=project_name, font=("Arial", 16), bg="#2C2C2C", fg="white")
project_name_label.pack(side=tk.TOP, anchor="w", padx=10, pady=10)

rectangle_info_canvas = tk.Canvas(left_frame, width=200, height=600, bg="#2C2C2C", highlightthickness=0)
rectangle_info_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

rectangle_info_frame = tk.Frame(rectangle_info_canvas, bg="#2C2C2C")
rectangle_info_canvas.create_window((0, 0), window=rectangle_info_frame, anchor="nw")

left_scrollbar = tk.Scrollbar(left_frame, orient=tk.VERTICAL, command=rectangle_info_canvas.yview)
## left_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
left_scrollbar.pack(side='right', fill='y')
rectangle_info_canvas.config(yscrollcommand=left_scrollbar.set)

def on_configure(event):
    rectangle_info_canvas.configure(scrollregion=rectangle_info_canvas.bbox("all"))

rectangle_info_frame.bind("<Configure>", on_configure)

# Canvas for rectangles
canvas_frame = tk.Frame(app, bg="#2C2C2C")
canvas_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

canvas = tk.Canvas(canvas_frame, bg="#F4F4F4", width=800, height=600, scrollregion=(0, 0, 2000, 2000))
canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

prev_x, prev_y = 0, 0

draw_mesh()

# Scrollbars for canvas
# hscrollbar = tk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL, command=canvas.xview)
# hscrollbar.pack(side=tk.BOTTOM, fill=tk.X)
# vscrollbar = tk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=canvas.yview)
# vscrollbar.pack(side=tk.RIGHT, fill=tk.Y)
# canvas.config(xscrollcommand=hscrollbar.set, yscrollcommand=vscrollbar.set)

# Mouse wheel event for zooming in and out
def on_mouse_wheel(event):
    scale_factor = 1.0
    if event.delta > 0:
        scale_factor = 1.1
    else:
        scale_factor = 0.9

    canvas.scale(tk.ALL, event.x, event.y, scale_factor, scale_factor)
    canvas.configure(scrollregion=canvas.bbox(tk.ALL))

canvas.bind("<MouseWheel>", on_mouse_wheel)

def on_canvas_click(event):
    global obj_grp,figure
    mesh_size = 20
    x, y = event.x, event.y

    # Snap to the nearest grid point
    x = round(x / mesh_size) * mesh_size
    y = round(y / mesh_size) * mesh_size

    # Draw a colored square around the clicked point
    square_size = mesh_size
    square = canvas.create_rectangle(x, y, x + square_size, y + square_size, outline="red", tags="clicked_point")
    
    cnt = 0
    flg = 0
    for item in canvas.find_withtag("rectangle"):
        # name = canvas.itemcget(item, "tags").split()[1]
        x1, y1, x2, y2 = canvas.coords(item)
        if x1 < x < x2+mesh_size and y1 < y < y2+mesh_size:
            flg = 1
            break
        cnt += 1
    if flg == 1:
        obj_grp[cnt].append(square)
    

def on_canvas_right_click(event):
    mesh_size = 20
    x, y = event.x, event.y

    print(f'right -> {x,y}')

    # Snap to the nearest grid point
    x = round(x / mesh_size) * mesh_size
    y = round(y / mesh_size) * mesh_size

    # Remove the colored square at the clicked point
    clicked_point = canvas.find_enclosed(x, y, x + mesh_size, y + mesh_size)
    for item in clicked_point:
        if "clicked_point" in canvas.gettags(item):
            print(f'delete -> {item}')
            canvas.delete(item)

canvas.bind("<Button-1>", on_canvas_click)
canvas.bind("<Button-3>", on_canvas_right_click)

def on_canvas_mouse_wheel(event):
    zoom_factor_per_scroll = 1.1

    # Get the current canvas scale
    current_scale = canvas.scale_x

    # Calculate the new scale
    if event.delta > 0:
        new_scale = current_scale * zoom_factor_per_scroll
    else:
        new_scale = current_scale / zoom_factor_per_scroll

    # Set the new scale for the canvas
    canvas.scale_x, canvas.scale_y = new_scale, new_scale
    canvas.configure(scale_x=new_scale, scale_y=new_scale)

# Remove the scrollbars
# main_frame.grid_forget()
canvas.grid(row=0, column=1, sticky="nsew")

canvas.bind("<MouseWheel>", on_canvas_mouse_wheel)


obj_grp = list()

app.mainloop()

