import random

class Position:
    def __init__(self, x: int, y: int, status: str):
        self.x = x
        self.y = y
        self.status = status

    def __repr__(self):
        return f"('{self.x}'/'{self.y}'/'{self.status}')"

class DataGrid:
    def __init__(self):
        self.size = 50
        self.grid = [
            [Position(x, y, "empty") for x in range(self.size)]
            for y in range(self.size)
        ]

        all_coords = [(x, y) for x in range(self.size) for y in range(self.size)]
        selected = random.sample(all_coords, 4)

        ai_coord = selected[0]
        item_coords = selected[1:]

        self.grid[ai_coord[1]][ai_coord[0]].status = "ai"
        for x, y in item_coords:
            self.grid[y][x].status = "item"

    def __repr__(self):
        result = ""
        for row in self.grid:
            row_str = " ".join(f"({pos.x}/{pos.y}/{pos.status})" for pos in row)
            result += row_str + "\n"
        return result