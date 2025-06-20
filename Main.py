import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import time
import math
import random
from datetime import datetime
from collections import deque
import os
import re

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class RobotApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Робот на складі")
        self.state('zoomed')

        self.grid_size = 50
        self.cell_size = 12

        self.robot_pos = None
        self.items = {}
        self.held_item = None  
        self.path_cells = []

        self.shelves = []

        self.delivery_points = [
            [41, 23],[42, 23],[43, 23],[44, 23],[46, 23],[47, 23],[48, 23],[49, 23],
            [49, 24],[49, 25],[49, 26],[49, 27],[49, 28],[49, 29],[49, 30],             
            [41, 30],[42, 30],[43, 30],[44, 30],[46, 30],[47, 30],[48, 30],      
            [41, 20],[41, 21],[41, 24],[41, 25],[41, 28],[41, 29],    

            [43, 25],[44, 25],[46, 25],[47, 25],
            [47, 26],[47, 27],[47, 28],
            [43, 28],[44, 28],[46, 28],[47, 28],
        ]

        self.initialize_positions()

        self.animation_speed = 0.03

        self.create_layout()

    def initialize_positions(self):
        self.robot_pos = None
        self.items = {}
        self.shelves = []

        self.generate_fixed_shelves()

        self.robot_pos = [45, 26]

        num_items = random.randint(5, 35)
        
        shuffled_shelves = self.shelves.copy()
        random.shuffle(shuffled_shelves)
        
        for i in range(min(num_items, len(shuffled_shelves))):
            item_id = f"item_{i}"
            item_color = "#08e8de"
            item_pos = shuffled_shelves[i]
            
            self.items[item_id] = {
                "color": item_color,
                "pos": item_pos,
                "delivered": False  # Флаг доставки
            }

    def generate_fixed_shelves(self):
        self.shelves = []

        for i in range(0, 50):
            if(i % 8 == 0):
                continue

            for j in range(-1, 50, 4):
                if(i > 40 and i < 50 and j > 20 and j < 30):
                    continue

                self.shelves.append([i,j+1])
                self.shelves.append([i,j+2])

    def create_layout(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.left_frame = ctk.CTkFrame(self)
        self.left_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        self.left_frame.grid_columnconfigure(0, weight=1)
        self.left_frame.grid_rowconfigure(0, weight=3)
        self.left_frame.grid_rowconfigure(1, weight=1)
        self.left_frame.grid_rowconfigure(2, weight=0)  # Новая строка для команд

        self.log_frame = ctk.CTkFrame(self.left_frame)
        self.log_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        self.log_label = ctk.CTkLabel(self.log_frame, text="Історія подій:", anchor="w")
        self.log_label.pack(padx=10, pady=5, anchor="w")

        self.log_text = ctk.CTkTextbox(self.log_frame, wrap="word")
        self.log_text.pack(padx=10, pady=5, fill="both", expand=True)

        self.buttons_frame = ctk.CTkFrame(self.left_frame)
        self.buttons_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

        button_width = 200
        button_height = 40

        self.select_item_btn = ctk.CTkButton(
            self.buttons_frame,
            text="Доставка предмета",
            command=self.start_item_selection,
            width=button_width,
            height=button_height
        )
        self.select_item_btn.pack(padx=10, pady=10)

        self.move_item_btn = ctk.CTkButton(
            self.buttons_frame,
            text="Доставити предмет",
            command=self.deliver_item,
            width=button_width,
            height=button_height,
            state="disabled" 
        )
        self.move_item_btn.pack(padx=10, pady=10)

        self.extra_btn = ctk.CTkButton(
            self.buttons_frame,
            text="Нова конфігурація",
            command=self.regenerate_configuration,
            width=button_width,
            height=button_height
        )
        self.extra_btn.pack(padx=10, pady=10)

        # Новая секция для текстовых команд
        self.commands_frame = ctk.CTkFrame(self.left_frame)
        self.commands_frame.grid(row=2, column=0, padx=10, pady=10, sticky="ew")

        self.command_label = ctk.CTkLabel(self.commands_frame, text="Текстові команди:", anchor="w")
        self.command_label.pack(padx=10, pady=5, anchor="w")

        self.command_entry = ctk.CTkEntry(
            self.commands_frame,
            placeholder_text="Введіть команду...",
            width=button_width,
            height=button_height
        )
        self.command_entry.pack(padx=10, pady=5, fill="x")
        
        # Привязка Enter к выполнению команды
        self.command_entry.bind("<Return>", self.execute_text_command)

        self.execute_cmd_btn = ctk.CTkButton(
            self.commands_frame,
            text="Виконати команду",
            command=self.execute_text_command,
            width=button_width,
            height=button_height
        )
        self.execute_cmd_btn.pack(padx=10, pady=5)

        self.right_frame = ctk.CTkFrame(self)
        self.right_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        self.grid_canvas = tk.Canvas(
            self.right_frame,
            bg="white",  
            highlightthickness=0
        )
        self.grid_canvas.pack(fill="both", expand=True, padx=10, pady=10)

        self.grid_canvas.bind("<Configure>", self.draw_grid)
        self.grid_canvas.bind("<Button-1>", self.canvas_click)

        self.selection_mode = None  

        self.add_log("Додаток запущено. Робот готовий до керування.")
        self.add_log(f"Створено {len(self.shelves)} стелажів.")
        self.add_log(f"Створено {len(self.items)} предметів на стелажах.")
        self.add_log(f"Позиція робота: {self.robot_pos}")

    def execute_text_command(self, event=None):
        """Обработка текстовых команд"""
        command = self.command_entry.get().strip().lower()
        
        if not command:
            messagebox.showwarning("Помилка", "Введіть команду!")
            return
        
        self.add_log(f"Отримана команда: {command}")
        
        # Паттерн для сбора ближайших n товаров
        pattern_nearest = r"собери\s+найближчi?\s+(\d+)\s+товари"
        match_nearest = re.search(pattern_nearest, command)
        
        if match_nearest:
            n = int(match_nearest.group(1))
            self.collect_nearest_items(n)
            self.command_entry.delete(0, tk.END)
            return
        
        # Паттерн для сбора всех товаров
        if "собери всi товари" in command or "собери всі товари" in command:
            self.collect_all_items()
            self.command_entry.delete(0, tk.END)
            return
        
        # Паттерн для создания txt файла с логами
        if "создай txt файл с логами" in command or "створи txt файл з логами" in command:
            self.create_log_file()
            self.command_entry.delete(0, tk.END)
            return
        
        # Если команда не распознана
        messagebox.showwarning("Помилка", 
            "Команда не розпізнана!\n\n"
            "Доступні команди:\n"
            "• собери ближайшие N товаров\n"
            "• собери все товары\n"
            "• создай txt файл с логами")

    def collect_nearest_items(self, n):
        """Сбор n ближайших предметов от текущей позиции робота"""
        if self.held_item:
            messagebox.showwarning("Помилка", "Робот вже тримає предмет! Спочатку доставте його.")
            return
        
        if not self.items:
            messagebox.showwarning("Помилка", "Немає предметів для збору!")
            return
        
        if n <= 0:
            messagebox.showwarning("Помилка", "Кількість товарів повинна бути більше 0!")
            return
        
        # Отключаем кнопки во время выполнения
        self.select_item_btn.configure(state="disabled")
        self.execute_cmd_btn.configure(state="disabled")
        
        self.add_log(f"Початок збору {n} ближайших товарів...")
        
        original_pos = self.robot_pos.copy()
        collected_count = 0
        total_time = 0
        total_distance = 0
        
        try:
            for _ in range(min(n, len(self.items))):
                if not self.items:
                    break
                
                # Находим ближайший предмет от текущей позиции
                nearest_item = self.find_nearest_item()
                if not nearest_item:
                    break
                
                # Собираем предмет
                collect_time, collect_distance = self.auto_collect_item(nearest_item)
                if collect_time > 0:
                    collected_count += 1
                    total_time += collect_time
                    total_distance += collect_distance
                    self.add_log(f"Зібрано {collected_count}/{min(n, len(self.items) + collected_count)} товарів")
                else:
                    self.add_log(f"Не вдалося зібрати товар {nearest_item}")
                    break
        
        except Exception as e:
            self.add_log(f"Помилка при зборі товарів: {str(e)}")
        
        finally:
            # Включаем кнопки обратно
            self.select_item_btn.configure(state="normal")
            self.execute_cmd_btn.configure(state="normal")
        
        self.add_log(f"Завершено збір товарів. Зібрано: {collected_count}, Час: {total_time:.2f} сек, Відстань: {total_distance} клітин")

    def collect_all_items(self):
        """Сбор всех предметов на карте"""
        if self.held_item:
            messagebox.showwarning("Помилка", "Робот вже тримає предмет! Спочатку доставте його.")
            return
        
        if not self.items:
            messagebox.showwarning("Помилка", "Немає предметів для збору!")
            return
        
        total_items = len(self.items)
        self.collect_nearest_items(total_items)

    def find_nearest_item(self):
        """Находит ближайший НЕдоставленный предмет от текущей позиции робота"""
        if not self.items:
            return None
        
        nearest_item = None
        min_distance = float('inf')
        
        for item_id, item_data in self.items.items():
            # Проверяем, что предмет не доставлен
            if item_data.get("delivered", False):
                continue
                
            item_pos = item_data["pos"]
            
            # Ищем доступную позицию рядом с предметом
            directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
            for dx, dy in directions:
                adjacent_pos = [item_pos[0] + dx, item_pos[1] + dy]
                if (0 <= adjacent_pos[0] < self.grid_size and 
                    0 <= adjacent_pos[1] < self.grid_size and 
                    adjacent_pos not in self.shelves):
                    
                    # Находим путь к этой позиции
                    path = self.find_path(self.robot_pos, adjacent_pos)
                    if path and len(path) < min_distance:
                        min_distance = len(path)
                        nearest_item = item_id
                        break
        
        return nearest_item

    def auto_collect_item(self, item_id):
        """Автоматически собирает указанный предмет"""
        if item_id not in self.items:
            return 0, 0
        
        # Проверяем, что предмет не доставлен
        if self.items[item_id].get("delivered", False):
            return 0, 0
        
        item_pos = self.items[item_id]["pos"]
        
        # Находим доступную позицию рядом с предметом
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
        adjacent_pos = None
        
        for dx, dy in directions:
            check_pos = [item_pos[0] + dx, item_pos[1] + dy]
            if (0 <= check_pos[0] < self.grid_size and 
                0 <= check_pos[1] < self.grid_size and 
                check_pos not in self.shelves):
                adjacent_pos = check_pos
                break
        
        if not adjacent_pos:
            return 0, 0
        
        # Находим путь к предмету
        path_to_item = self.find_path(self.robot_pos, adjacent_pos)
        if not path_to_item:
            return 0, 0
        
        start_time = time.time()
        
        # Движение к предмету
        for step in path_to_item[1:]:
            self.robot_pos = step
            self.path_cells.append(step.copy())
            self.draw_grid()
            self.update()
            time.sleep(self.animation_speed)
        
        # Берем предмет
        self.held_item = item_id
        self.add_log(f"Робот взяв предмет {item_id} з позиції {item_pos}")
        
        # Находим ближайшую точку доставки
        best_target = self.find_nearest_delivery_point()
        if not best_target:
            return 0, 0
        
        # Находим путь к точке доставки
        path_to_delivery = self.find_path(self.robot_pos, best_target)
        if not path_to_delivery:
            return 0, 0
        
        # Движение к точке доставки
        for step in path_to_delivery[1:]:
            self.robot_pos = step
            self.path_cells.append(step.copy())
            self.draw_grid()
            self.update()
            time.sleep(self.animation_speed)
        
        # Доставляем предмет и помечаем как delivered
        self.items[self.held_item]["pos"] = self.robot_pos.copy()
        self.items[self.held_item]["delivered"] = True  # Помечаем как доставленный
        self.held_item = None
        
        end_time = time.time()
        total_time = end_time - start_time
        total_distance = len(path_to_item) + len(path_to_delivery) - 2
        
        self.add_log(f"Предмет {item_id} доставлен на {self.robot_pos}")
        self.draw_grid()
        
        return total_time, total_distance

    def find_nearest_delivery_point(self):
        """Находит ближайшую доступную точку доставки"""
        best_target = None
        best_distance = float('inf')
        
        for target in self.delivery_points:
            if target in self.shelves:
                continue
            
            # Проверяем, не занята ли позиция
            position_occupied = False
            for item_id, item_data in self.items.items():
                if item_data["pos"] == target and item_id != self.held_item:
                    position_occupied = True
                    break
            
            if position_occupied:
                continue
            
            path = self.find_path(self.robot_pos, target)
            if path and len(path) < best_distance:
                best_distance = len(path)
                best_target = target
        
        return best_target

    def create_log_file(self):
        """Создает txt файл с логами событий"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"robot_logs_{timestamp}.txt"
            
            # Получаем содержимое лога
            log_content = self.log_text.get("1.0", tk.END)
            
            # Записываем в файл
            with open(filename, 'w', encoding='utf-8') as file:
                file.write(f"Логи роботи робота на складі\n")
                file.write(f"Створено: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n")
                file.write("=" * 50 + "\n\n")
                file.write(log_content)
            
            current_dir = os.getcwd()
            full_path = os.path.join(current_dir, filename)
            
            self.add_log(f"Файл з логами створено: {filename}")
            self.add_log(f"Шлях до файлу: {full_path}")
            
            messagebox.showinfo("Успіх", f"Файл з логами створено:\n{filename}")
            
        except Exception as e:
            error_msg = f"Помилка при створенні файлу: {str(e)}"
            self.add_log(error_msg)
            messagebox.showerror("Помилка", error_msg)

    def draw_grid(self, event=None):
        self.grid_canvas.delete("all")

        canvas_width = self.grid_canvas.winfo_width()
        canvas_height = self.grid_canvas.winfo_height()

        available_size = min(canvas_width, canvas_height) - 40  
        self.cell_size = available_size / self.grid_size

        offset_x = (canvas_width - self.cell_size * self.grid_size) / 2
        offset_y = (canvas_height - self.cell_size * self.grid_size) / 2

        for i in range(self.grid_size + 1):
            x = offset_x + i * self.cell_size
            self.grid_canvas.create_line(
                x, offset_y,
                x, offset_y + self.grid_size * self.cell_size,
                fill="#CCCCCC",
            )

            y = offset_y + i * self.cell_size
            self.grid_canvas.create_line(
                offset_x, y,
                offset_x + self.grid_size * self.cell_size, y,
                fill="#CCCCCC"
            )

        for i in range(0, self.grid_size + 1, 5):
            x = offset_x + i * self.cell_size
            self.grid_canvas.create_text(
                x, offset_y + self.grid_size * self.cell_size + 15,
                text=str(i),
                fill="black"
            )

            y = offset_y + i * self.cell_size
            self.grid_canvas.create_text(
                offset_x - 15, y,
                text=str(i),
                fill="black"
            )

        self.highlight_empty_delivery_points(offset_x, offset_y)

        for shelf in self.shelves:
            x, y = shelf
            shelf_x = offset_x + x * self.cell_size
            shelf_y = offset_y + y * self.cell_size
            self.grid_canvas.create_rectangle(
                shelf_x, shelf_y,
                shelf_x + self.cell_size, shelf_y + self.cell_size,
                fill="#8B4513", outline="#654321"  
            )

        for cell in self.path_cells:
            x, y = cell
            cell_x = offset_x + x * self.cell_size
            cell_y = offset_y + y * self.cell_size
            self.grid_canvas.create_rectangle(
                cell_x, cell_y,
                cell_x + self.cell_size, cell_y + self.cell_size,
                fill="#FFFF00", outline="", stipple="gray50"
            )

        for item_id, item_data in self.items.items():
            if self.held_item == item_id:
                continue

            x, y = item_data["pos"]
            item_x = offset_x + x * self.cell_size
            item_y = offset_y + y * self.cell_size

            fill_color = item_data["color"]

            margin = self.cell_size * 0.2
            self.grid_canvas.create_rectangle(
                item_x + margin, item_y + margin,
                item_x + self.cell_size - margin, item_y + self.cell_size - margin,
                fill=fill_color, outline="black", width=1  
            )

        robot_x = offset_x + self.robot_pos[0] * self.cell_size
        robot_y = offset_y + self.robot_pos[1] * self.cell_size
        self.grid_canvas.create_oval(
            robot_x, robot_y,
            robot_x + self.cell_size, robot_y + self.cell_size,
            fill="#FF0000", outline="black"
        )

        if self.held_item:
            held_color = self.items[self.held_item]["color"]

            center_x = robot_x + self.cell_size / 2
            center_y = robot_y + self.cell_size / 2
            self.grid_canvas.create_oval(
                center_x - self.cell_size / 4, center_y - self.cell_size / 4,
                center_x + self.cell_size / 4, center_y + self.cell_size / 4,
                fill=held_color, outline="black"
            )

        self.grid_offset_x = offset_x
        self.grid_offset_y = offset_y

    def highlight_empty_delivery_points(self, offset_x, offset_y):
        occupied_positions = set()
        for item_id, item_data in self.items.items():
            occupied_positions.add(tuple(item_data["pos"]))
        
        occupied_positions.add(tuple(self.robot_pos))
        
        for delivery_point in self.delivery_points:
            if (tuple(delivery_point) not in occupied_positions and 
                delivery_point not in self.shelves):
                
                x, y = delivery_point
                point_x = offset_x + x * self.cell_size
                point_y = offset_y + y * self.cell_size
                
                self.grid_canvas.create_rectangle(
                    point_x, point_y,
                    point_x + self.cell_size, point_y + self.cell_size,
                    fill="#C0C0C0", outline="#808080", width=1  
                )

    def canvas_click(self, event):
        if not self.selection_mode:
            return

        x = int((event.x - self.grid_offset_x) / self.cell_size)
        y = int((event.y - self.grid_offset_y) / self.cell_size)

        if 0 <= x < self.grid_size and 0 <= y < self.grid_size:
            if self.selection_mode == "select_item":
                self.execute_item_selection(x, y)

        self.selection_mode = None

    def start_item_selection(self):
        if self.held_item:
            messagebox.showwarning("Помилка", "Робот вже тримає предмет! Спочатку доставте його.")
            return

        if not self.items:
            messagebox.showwarning("Помилка", "Немає предметів для доставки!")
            return

        self.add_log("Виберіть предмет для доставки (клікніть на стелаж з предметом)")
        self.selection_mode = "select_item"

    def execute_item_selection(self, x, y):
        selected_item = None
        for item_id, item_data in self.items.items():
            if item_data["pos"][0] == x and item_data["pos"][1] == y:
                selected_item = item_id
                break

        if not selected_item:
            messagebox.showwarning("Помилка", "На цій клітині немає предмета!")
            return

        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
        adjacent_pos = None
        
        for dx, dy in directions:
            check_pos = [x + dx, y + dy]
            if (0 <= check_pos[0] < self.grid_size and 
                0 <= check_pos[1] < self.grid_size and 
                check_pos not in self.shelves):
                adjacent_pos = check_pos
                break
        
        if not adjacent_pos:
            self.add_log(f"Неможливо підійти до предмета на [{x}, {y}]")
            return
        
        path = self.find_path(self.robot_pos, adjacent_pos)
        if not path:
            messagebox.showwarning("Помилка", "Неможливо знайти шлях до предмета!")
            return

        start_time = time.time()
        for step in path[1:]:
            self.robot_pos = step
            self.path_cells.append(step.copy())
            self.draw_grid()
            self.update()
            time.sleep(self.animation_speed)
        
        self.held_item = selected_item
        self.move_item_btn.configure(state="normal")
        self.select_item_btn.configure(state="disabled")
        
        end_time = time.time()
        duration = end_time - start_time
        
        self.add_log(f"Робот підійшов до предмета на [{x}, {y}]. Час: {duration:.2f} сек.")
        self.add_log(f"Робот взяв предмет з стелажа")
        self.draw_grid()

    def deliver_item(self):
        if not self.held_item:
            messagebox.showwarning("Помилка", "Робот не тримає предмет!")
            return

        best_target = None
        best_distance = float('inf')
        best_path = None
        
        for target in self.delivery_points:
            if target in self.shelves:
                continue
            
            position_occupied = False
            for item_id, item_data in self.items.items():
                if item_data["pos"] == target and item_id != self.held_item:
                    position_occupied = True
                    break
            
            if position_occupied:
                continue
                
            path = self.find_path(self.robot_pos, target)
            if path and len(path) < best_distance:
                best_distance = len(path)
                best_target = target
                best_path = path
        
        if not best_target:
            messagebox.showwarning("Помилка", "Немає доступних місць для доставки!")
            return
        
        start_time = time.time()
        
        for step in best_path[1:]:
            self.robot_pos = step
            self.path_cells.append(step.copy())
            self.draw_grid()
            self.update()
            time.sleep(self.animation_speed)
        
        end_time = time.time()
        duration = end_time - start_time
        
        if self.held_item:
            self.items[self.held_item]["pos"] = self.robot_pos.copy()
            self.held_item = None
            self.move_item_btn.configure(state="disabled")
            self.select_item_btn.configure(state="normal")
            self.add_log(f"Предмет доставлен та розміщений на {self.robot_pos}")
            self.add_log(f"Час доставки: {duration:.2f} сек. Пройдено {len(best_path) - 1} клітин.")
            self.draw_grid()

    def regenerate_configuration(self):
        self.path_cells = []

        if self.held_item:
            directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
            random.shuffle(directions)

            for dx, dy in directions:
                nx, ny = self.robot_pos[0] + dx, self.robot_pos[1] + dy
                if 0 <= nx < self.grid_size and 0 <= ny < self.grid_size and [nx, ny] not in self.shelves:
                    self.items[self.held_item]["pos"] = [nx, ny]
                    self.add_log(f"Предмет розміщений поруч з роботом на [{nx}, {ny}]")
                    self.held_item = None
                    self.move_item_btn.configure(state="disabled")
                    self.select_item_btn.configure(state="normal")
                    break

        self.initialize_positions()

        self.add_log("Згенерована нова конфігурація.")
        self.add_log(f"Створено {len(self.shelves)} стелажів.")
        self.add_log(f"Створено {len(self.items)} предметів на стелажах.")
        self.add_log(f"Нова позиція робота: {self.robot_pos}")

        self.draw_grid()

    def add_log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"

        self.log_text.insert(tk.END, log_entry)

        self.log_text.see(tk.END)

    def find_path(self, start, end):
        if start == end:
            return [start]

        if [end[0], end[1]] in self.shelves:
            return []

        occupied_positions = set()
        for item_id, item_data in self.items.items():
            if item_id != self.held_item:
                occupied_positions.add(tuple(item_data["pos"]))

        queue = deque([[start]])
        visited = set([tuple(start)])

        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]

        while queue:
            path = queue.popleft()
            current = path[-1]

            if current[0] == end[0] and current[1] == end[1]:
                return path

            for dx, dy in directions:
                nx, ny = current[0] + dx, current[1] + dy
                new_pos = [nx, ny]

                if (0 <= nx < self.grid_size and 0 <= ny < self.grid_size and
                        tuple(new_pos) not in visited and
                        new_pos not in self.shelves and
                        tuple(new_pos) not in occupied_positions):
                    new_path = path.copy()
                    new_path.append(new_pos)
                    queue.append(new_path)
                    visited.add(tuple(new_pos))

        return []


if __name__ == "__main__":
    app = RobotApp()
    app.mainloop()