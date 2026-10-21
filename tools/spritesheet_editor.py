import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk
from PIL import Image, ImageTk
import json
import collections
import os


class SpritesheetSelectorApp:
    def __init__(self, master):
        self.master = master
        master.title("Spritesheet Editor")

        self.project_data = {
            "project_name": "Nuevo Proyecto",
            "spritesheet_path": None,
            "character_name": "",
            "animations": collections.defaultdict(list)
        }

        self.tk_spritesheet_image = None
        self.rect_ids = {}
        self.start_x = None
        self.start_y = None
        self.current_rect_id = None
        self.drawing_mode = False
        self.fixed_size_mode = False

        self.create_widgets()

    def create_widgets(self):
        main_paned_window = tk.PanedWindow(self.master, orient=tk.HORIZONTAL, sashrelief=tk.RAISED)
        main_paned_window.pack(fill=tk.BOTH, expand=True)

        left_frame = tk.Frame(main_paned_window)
        main_paned_window.add(left_frame, stretch="always")

        self.canvas = tk.Canvas(left_frame, bg="gray", cursor="cross")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.bind("<ButtonPress-1>", self.on_press_left)
        self.canvas.bind("<B1-Motion>", self.on_drag_left)
        self.canvas.bind("<ButtonRelease-1>", self.on_release_left)
        self.canvas.bind("<Button-3>", self.on_press_right)

        right_frame = tk.Frame(main_paned_window, width=400)
        main_paned_window.add(right_frame, stretch="never")

        top_controls_frame = tk.Frame(right_frame)
        top_controls_frame.pack(fill=tk.X, pady=5)
        tk.Button(top_controls_frame, text="Cargar Spritesheet", command=self.load_spritesheet).pack(side=tk.LEFT,
                                                                                                     padx=5, fill=tk.X,
                                                                                                     expand=True)
        tk.Button(top_controls_frame, text="Sugerir Sprites", command=self.suggest_sprites).pack(side=tk.LEFT, padx=5,
                                                                                                 fill=tk.X, expand=True)
        tk.Button(top_controls_frame, text="Guardar JSON", command=self.save_json).pack(side=tk.LEFT, padx=5, fill=tk.X,
                                                                                        expand=True)

        project_frame = tk.LabelFrame(right_frame, text="Información del Proyecto")
        project_frame.pack(fill=tk.X, padx=5, pady=5)

        tk.Label(project_frame, text="Nombre del Personaje:").pack(side=tk.LEFT, padx=5)
        self.character_name_entry = tk.Entry(project_frame)
        self.character_name_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        drawing_frame = tk.LabelFrame(right_frame, text="Modo de Selección")
        drawing_frame.pack(fill=tk.X, padx=5, pady=5)
        self.drawing_mode_btn = tk.Button(drawing_frame, text="Modo Libre (Mouse)", command=self.toggle_drawing_mode,
                                          relief=tk.RAISED)
        self.drawing_mode_btn.pack(side=tk.LEFT, padx=5)
        self.fixed_size_btn = tk.Button(drawing_frame, text="Modo de Tamaño Fijo", command=self.toggle_fixed_size_mode,
                                        relief=tk.RAISED)
        self.fixed_size_btn.pack(side=tk.LEFT, padx=5)
        self.size_entry_frame = tk.Frame(drawing_frame)
        self.size_entry_frame.pack(side=tk.LEFT)
        tk.Label(self.size_entry_frame, text="Ancho:").pack(side=tk.LEFT)
        self.width_entry = tk.Entry(self.size_entry_frame, width=5)
        self.width_entry.pack(side=tk.LEFT)
        tk.Label(self.size_entry_frame, text="Alto:").pack(side=tk.LEFT)
        self.height_entry = tk.Entry(self.size_entry_frame, width=5)
        self.height_entry.pack(side=tk.LEFT)

        sprite_panel_frame = tk.LabelFrame(right_frame, text="Sprites Guardados")
        sprite_panel_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.sprite_listbox = tk.Listbox(sprite_panel_frame, selectmode=tk.EXTENDED)
        self.sprite_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.sprite_listbox.bind('<<ListboxSelect>>', self.on_sprite_select)
        scrollbar = tk.Scrollbar(sprite_panel_frame, orient=tk.VERTICAL)
        scrollbar.config(command=self.sprite_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.sprite_listbox.config(yscrollcommand=scrollbar.set)

        panel_buttons_frame = tk.Frame(right_frame)
        panel_buttons_frame.pack(fill=tk.X, pady=5)
        tk.Button(panel_buttons_frame, text="Eliminar", command=self.delete_selected_sprite).pack(side=tk.LEFT, padx=5,
                                                                                                  fill=tk.X,
                                                                                                  expand=True)
        tk.Button(panel_buttons_frame, text="Modificar", command=self.edit_selected_sprite).pack(side=tk.LEFT, padx=5,
                                                                                                 fill=tk.X, expand=True)

        anim_frame = tk.LabelFrame(right_frame, text="Gestión de Animaciones")
        anim_frame.pack(fill=tk.X, padx=5, pady=5)
        tk.Button(anim_frame, text="Agrupar en Animación", command=self.group_sprites_to_animation).pack(fill=tk.X,
                                                                                                         padx=5, pady=2)
        tk.Label(anim_frame, text="Nombre de la animación:").pack(side=tk.LEFT, padx=5)
        self.anim_name_entry = tk.Entry(anim_frame)
        self.anim_name_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

    def toggle_drawing_mode(self):
        self.drawing_mode = not self.drawing_mode
        if self.drawing_mode:
            self.drawing_mode_btn.config(relief=tk.SUNKEN)
            self.fixed_size_mode = False
            self.fixed_size_btn.config(relief=tk.RAISED)
        else:
            self.drawing_mode_btn.config(relief=tk.RAISED)
        self.canvas.config(cursor="cross" if self.drawing_mode else "arrow")
        if self.current_rect_id:
            self.canvas.delete(self.current_rect_id)
            self.current_rect_id = None

    def toggle_fixed_size_mode(self):
        self.fixed_size_mode = not self.fixed_size_mode
        if self.fixed_size_mode:
            self.fixed_size_btn.config(relief=tk.SUNKEN)
            self.drawing_mode = False
            self.drawing_mode_btn.config(relief=tk.RAISED)
        else:
            self.fixed_size_btn.config(relief=tk.RAISED)
        self.canvas.config(cursor="cross" if self.fixed_size_mode else "arrow")
        if self.current_rect_id:
            self.canvas.delete(self.current_rect_id)
            self.current_rect_id = None

    def load_spritesheet(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.png *.jpg *.jpeg")])
        if file_path:
            self.project_data['spritesheet_path'] = file_path
            self.project_data['animations'].clear()
            self.character_name_entry.delete(0, tk.END)
            self.sprite_listbox.delete(0, tk.END)
            self.canvas.delete("all")
            self.rect_ids.clear()
            try:
                self.spritesheet_image = Image.open(self.project_data['spritesheet_path'])
                self.tk_spritesheet_image = ImageTk.PhotoImage(self.spritesheet_image)
                self.canvas.config(width=self.spritesheet_image.width, height=self.spritesheet_image.height)
                self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_spritesheet_image)
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo cargar la imagen: {e}")

    def on_press_left(self, event):
        if not self.project_data['spritesheet_path']:
            return

        if not self.drawing_mode and not self.fixed_size_mode:
            # Buscar si se ha hecho clic en un rectángulo existente
            clicked_items = self.canvas.find_closest(event.x, event.y)
            if clicked_items:
                clicked_item = clicked_items[0]
                # Buscar el sprite por su ID de rectángulo
                for sprite_name, rect_id in self.rect_ids.items():
                    if rect_id == clicked_item:
                        # Resaltar el sprite en la lista
                        self.select_sprite_in_listbox(sprite_name)
                        # También puedes resaltar el rectángulo en el canvas
                        self.canvas.itemconfig(rect_id, outline="blue")
                        return

        # Si no se hizo clic en un rectángulo existente o si estamos en modo de dibujo
        self.start_x = event.x
        self.start_y = event.y
        if self.current_rect_id:
            self.canvas.delete(self.current_rect_id)
        if self.drawing_mode or self.fixed_size_mode:
            self.current_rect_id = self.canvas.create_rectangle(self.start_x, self.start_y, self.start_x, self.start_y,
                                                                outline="red", width=2)

    def select_sprite_in_listbox(self, sprite_name):
        self.sprite_listbox.selection_clear(0, tk.END)
        for i in range(self.sprite_listbox.size()):
            item = self.sprite_listbox.get(i)
            # Manejar tanto los títulos de animación como los nombres de sprites
            if item == sprite_name:
                self.sprite_listbox.selection_set(i)
                self.sprite_listbox.see(i)  # Hacer scroll hasta el elemento
                break
            elif item.startswith("---") and f"--- Animación: {sprite_name.upper()} ---" == item:
                self.sprite_listbox.selection_set(i)
                self.sprite_listbox.see(i)
                break

    def on_drag_left(self, event):
        if not self.project_data['spritesheet_path'] or not self.current_rect_id:
            return
        if self.drawing_mode:
            self.canvas.coords(self.current_rect_id, self.start_x, self.start_y, event.x, event.y)
        elif self.fixed_size_mode:
            try:
                width = int(self.width_entry.get())
                height = int(self.height_entry.get())
                self.canvas.coords(self.current_rect_id, self.start_x, self.start_y, self.start_x + width,
                                   self.start_y + height)
            except ValueError:
                pass

    def on_release_left(self, event):
        if not self.project_data['spritesheet_path'] or not self.current_rect_id:
            return
        x1, y1, x2, y2 = self.canvas.coords(self.current_rect_id)
        x1 = min(x1, x2)
        y1 = min(y1, y2)
        x2 = max(x1, x2)
        y2 = max(y1, y2)
        width = x2 - x1
        height = y2 - y1
        if width > 0 and height > 0:
            sprite_data = {
                "x": int(x1), "y": int(y1), "width": int(width), "height": int(height),
                "name": f"sprite_{len(self.get_all_sprites())}", "description": "", "animation": "default"
            }
            self.add_sprite_to_list(sprite_data, self.current_rect_id)
            self.current_rect_id = None
        else:
            self.canvas.delete(self.current_rect_id)
            self.current_rect_id = None

    def get_all_sprites(self):
        all_sprites = []
        for anim_list in self.project_data['animations'].values():
            all_sprites.extend(anim_list)
        return all_sprites

    def on_press_right(self, event):
        item = self.canvas.find_closest(event.x, event.y)[0]
        if item in self.rect_ids.values():
            for sprite_data in self.get_all_sprites():
                if self.rect_ids.get(sprite_data['name']) == item:
                    self.delete_sprite(sprite_data['name'])
                    return

    def on_sprite_select(self, event):
        for rect_id in self.rect_ids.values():
            self.canvas.itemconfig(rect_id, outline="red")

        selected_names = [self.sprite_listbox.get(i) for i in self.sprite_listbox.curselection()]
        for name in selected_names:
            rect_id = self.rect_ids.get(name)
            if rect_id:
                self.canvas.itemconfig(rect_id, outline="blue")

    def add_sprite_to_list(self, sprite_data, rect_id):
        anim_name = sprite_data.get('animation', 'default')
        if anim_name not in self.project_data['animations']:
            self.project_data['animations'][anim_name] = []
        self.project_data['animations'][anim_name].append(sprite_data)
        self.rect_ids[sprite_data['name']] = rect_id
        self.update_sprite_listbox()
        self.redraw_sprites()

    def delete_selected_sprite(self):
        selected_names = [self.sprite_listbox.get(i) for i in self.sprite_listbox.curselection()]
        if not selected_names:
            messagebox.showinfo("Error", "Selecciona al menos un sprite para eliminar.")
            return

        for sprite_name in selected_names:
            self.delete_sprite(sprite_name)

        self.update_sprite_listbox()

    def delete_sprite(self, sprite_name):
        found = False
        for anim_name in list(self.project_data['animations'].keys()):
            for i, sprite_data in enumerate(self.project_data['animations'][anim_name]):
                if sprite_data['name'] == sprite_name:
                    del self.project_data['animations'][anim_name][i]
                    if not self.project_data['animations'][anim_name]:
                        del self.project_data['animations'][anim_name]
                    found = True
                    break
            if found:
                break

        if found:
            rect_id = self.rect_ids.get(sprite_name)
            if rect_id:
                self.canvas.delete(rect_id)
                del self.rect_ids[sprite_name]

    def edit_selected_sprite(self):
        selected_index = self.sprite_listbox.curselection()
        if not selected_index:
            messagebox.showinfo("Error", "Selecciona un sprite para modificar.")
            return

        sprite_name = self.sprite_listbox.get(selected_index[0])
        old_sprite_data = None
        for anim_list in self.project_data['animations'].values():
            for sprite_data in anim_list:
                if sprite_data['name'] == sprite_name:
                    old_sprite_data = sprite_data
                    break
            if old_sprite_data:
                break

        if not old_sprite_data:
            return

        self.show_edit_dialog(old_sprite_data)

    def show_edit_dialog(self, sprite_data):
        dialog = tk.Toplevel(self.master)
        dialog.title("Modificar Sprite")

        tk.Label(dialog, text="Nombre:").grid(row=0, column=0, padx=5, pady=5)
        name_entry = tk.Entry(dialog)
        name_entry.grid(row=0, column=1, padx=5, pady=5)
        name_entry.insert(0, sprite_data['name'])

        tk.Label(dialog, text="Descripción:").grid(row=1, column=0, padx=5, pady=5)
        desc_entry = tk.Entry(dialog)
        desc_entry.grid(row=1, column=1, padx=5, pady=5)
        desc_entry.insert(0, sprite_data['description'])

        tk.Label(dialog, text="Animación:").grid(row=2, column=0, padx=5, pady=5)
        anim_entry = tk.Entry(dialog)
        anim_entry.grid(row=2, column=1, padx=5, pady=5)
        anim_entry.insert(0, sprite_data['animation'])

        def save_changes():
            new_name = name_entry.get().strip()
            new_desc = desc_entry.get().strip()
            new_anim = anim_entry.get().strip()

            is_new_name = new_name != sprite_data['name']
            is_new_anim = new_anim != sprite_data['animation']

            if is_new_name or is_new_anim:
                old_anim_list = self.project_data['animations'][sprite_data['animation']]
                old_anim_list.remove(sprite_data)

                if not old_anim_list:
                    del self.project_data['animations'][sprite_data['animation']]

                sprite_data['animation'] = new_anim
                sprite_data['name'] = new_name

                if new_anim not in self.project_data['animations']:
                    self.project_data['animations'][new_anim] = []
                self.project_data['animations'][new_anim].append(sprite_data)

                if is_new_name:
                    rect_id = self.rect_ids.pop(sprite_data['name'])
                    self.rect_ids[new_name] = rect_id

            sprite_data['description'] = new_desc

            self.update_sprite_listbox()
            self.redraw_sprites()
            dialog.destroy()

        tk.Button(dialog, text="Guardar", command=save_changes).grid(row=3, column=0, columnspan=2, pady=10)

    def group_sprites_to_animation(self):
        selected_indices = self.sprite_listbox.curselection()
        if not selected_indices:
            messagebox.showinfo("Error", "Selecciona al menos un sprite para agrupar.")
            return

        anim_name = self.anim_name_entry.get().strip()
        if not anim_name:
            messagebox.showinfo("Error", "Ingresa un nombre para la animación.")
            return

        selected_sprites_names = [self.sprite_listbox.get(i) for i in selected_indices]

        sprites_to_move = []
        for name in selected_sprites_names:
            for anim_list in self.project_data['animations'].values():
                for sprite_data in anim_list:
                    if sprite_data['name'] == name:
                        sprites_to_move.append(sprite_data)
                        break

        for sprite_data in sprites_to_move:
            old_anim_list = self.project_data['animations'][sprite_data['animation']]
            old_anim_list.remove(sprite_data)
            sprite_data['animation'] = anim_name
            self.project_data['animations'][anim_name].append(sprite_data)

        self.project_data['animations'] = {k: v for k, v in self.project_data['animations'].items() if v}
        self.update_sprite_listbox()
        self.redraw_sprites()
        messagebox.showinfo("Agrupado", f"Sprites agrupados en la animación '{anim_name}'.")

    def update_sprite_listbox(self):
        self.sprite_listbox.delete(0, tk.END)
        for anim_name, sprites_list in self.project_data['animations'].items():
            self.sprite_listbox.insert(tk.END, f"--- Animación: {anim_name.upper()} ---")
            for sprite in sprites_list:
                self.sprite_listbox.insert(tk.END, sprite['name'])

    def redraw_sprites(self):
        self.canvas.delete("all")
        if self.tk_spritesheet_image:
            self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_spritesheet_image)
        self.rect_ids.clear()

        for anim_name, sprites_list in self.project_data['animations'].items():
            for sprite_data in sprites_list:
                rect_id = self.canvas.create_rectangle(
                    sprite_data["x"], sprite_data["y"],
                    sprite_data["x"] + sprite_data["width"], sprite_data["y"] + sprite_data["height"],
                    outline="red", width=2
                )
                self.rect_ids[sprite_data['name']] = rect_id

    def suggest_sprites(self):
        if not self.project_data['spritesheet_path']:
            messagebox.showinfo("Info", "Primero carga una spritesheet.")
            return

        self.project_data['animations'].clear()
        self.canvas.delete("all")
        self.rect_ids.clear()
        self.sprite_listbox.delete(0, tk.END)

        image = Image.open(self.project_data['spritesheet_path'])
        pixels = image.load()
        width, height = image.size
        visited = [[False for _ in range(height)] for _ in range(width)]

        def find_sprite(start_x, start_y):
            if visited[start_x][start_y]: return None
            if image.mode == "RGBA" and pixels[start_x, start_y][3] == 0: return None

            q = collections.deque([(start_x, start_y)])
            visited[start_x][start_y] = True
            min_x, min_y, max_x, max_y = start_x, start_y, start_x, start_y

            while q:
                x, y = q.popleft()
                min_x = min(min_x, x);
                min_y = min(min_y, y)
                max_x = max(max_x, x);
                max_y = max(max_y, y)

                for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < width and 0 <= ny < height and not visited[nx][ny]:
                        if image.mode == "RGBA":
                            if pixels[nx, ny][3] > 0:
                                visited[nx][ny] = True
                                q.append((nx, ny))
                        else:
                            visited[nx][ny] = True
                            q.append((nx, ny))
            return min_x, min_y, max_x - min_x + 1, max_y - min_y + 1

        for x in range(width):
            for y in range(height):
                rect = find_sprite(x, y)
                if rect:
                    sprite_data = {
                        "x": rect[0], "y": rect[1], "width": rect[2], "height": rect[3],
                        "name": f"sprite_{len(self.get_all_sprites())}",
                        "description": "Sugerido",
                        "animation": "default"
                    }
                    rect_id = self.canvas.create_rectangle(rect[0], rect[1], rect[0] + rect[2], rect[1] + rect[3],
                                                           outline="green", width=2)
                    self.add_sprite_to_list(sprite_data, rect_id)

        messagebox.showinfo("Sugerencia", f"Se encontraron {len(self.get_all_sprites())} sprites sugeridos.")
        self.redraw_sprites()
        self.update_sprite_listbox()

    def save_json(self):
        if not self.project_data['spritesheet_path']:
            messagebox.showinfo("Información", "No hay spritesheet cargada.")
            return

        project_name = simpledialog.askstring("Nombre del Proyecto", "Introduce el nombre del proyecto:",
                                              initialvalue=self.project_data['project_name'])
        if not project_name:
            return

        self.project_data['project_name'] = project_name

        character_name = self.character_name_entry.get().strip()
        if not character_name:
            messagebox.showinfo("Error", "Por favor, ingresa un nombre para el personaje.")
            return
        self.project_data['character_name'] = character_name

        file_path = filedialog.asksaveasfilename(
            initialfile=f"{project_name}.json",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")]
        )

        if file_path:
            serializable_data = {
                "project_name": self.project_data['project_name'],
                "spritesheet_path": self.project_data['spritesheet_path'],
                "character_name": self.project_data['character_name'],
                "animations": {
                    anim_name: anim_list for anim_name, anim_list in self.project_data['animations'].items()
                }
            }

            with open(file_path, "w") as f:
                json.dump(serializable_data, f, indent=4)

            messagebox.showinfo("Guardado", f"Archivo JSON guardado en: {file_path}")


if __name__ == "__main__":
    root = tk.Tk()
    app = SpritesheetSelectorApp(root)
    root.mainloop()
