from PIL import Image, ImageDraw, ImageFont
import time
import random
from digitalio import DigitalInOut, Direction
from adafruit_rgb_display import st7789
import board

class Game:
    def __init__(self):
        self.cs_pin = DigitalInOut(board.CE0)
        self.dc_pin = DigitalInOut(board.D25)
        self.reset_pin = DigitalInOut(board.D24)
        self.BAUDRATE = 24000000

        self.spi = board.SPI()
        self.disp = st7789.ST7789(
                    self.spi,
                    height=240,
                    y_offset=80,
                    rotation=180,
                    cs=self.cs_pin,
                    dc=self.dc_pin,
                    rst=self.reset_pin,
                    baudrate=self.BAUDRATE,
                    )
        # Input pins:
        self.button_A = DigitalInOut(board.D5)
        self.button_A.direction = Direction.INPUT

        self.button_B = DigitalInOut(board.D6)
        self.button_B.direction = Direction.INPUT

        self.button_U = DigitalInOut(board.D17)
        self.button_U.direction = Direction.INPUT

        self.button_D = DigitalInOut(board.D22)
        self.button_D.direction = Direction.INPUT

        self.button_L = DigitalInOut(board.D27)
        self.button_L.direction = Direction.INPUT

        self.button_R = DigitalInOut(board.D23)
        self.button_R.direction = Direction.INPUT

        self.backlight = DigitalInOut(board.D26)
        self.backlight.switch_to_output()
        self.backlight.value = True

        self.width = self.disp.width
        self.height = self.disp.height

        self.board = [[0 for _ in range(16)] for _ in range(16)]
        self.displayed = [[0 for _ in range(16)] for _ in range(16)]
        self.flags = [[0 for _ in range(16)] for _ in range(16)]
        self.cursor = [0, 0]

        self.images = {
            "boomball": Image.open("image/boomball.png").resize((15,15)),
            "flag": Image.open("image/new_emblem.png").resize((15,15)),
            "clear": Image.open("image/clear.png").resize((240,240)),
            "failed": Image.open("image/failed.png").resize((240,240)),
            "main": Image.open("image/main.png").resize((240,240)),
        }

        self.font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 14)

        self.game_over = False

        self.init_game()

    def init_game(self):
        self.place_bombs()
        self.calculate_beside_bombs()

    def place_bombs(self):
        for _ in range(40): # 폭탄 갯수
            while True:
                x, y = random.randint(0, 15), random.randint(0, 15)
                if self.board[y][x] == 0:
                    self.board[y][x] = 9
                    break

    def calculate_beside_bombs(self):
        for y in range(16):
            for x in range(16):
                if self.board[y][x] == 9:
                    continue
                count = 0
                for dx in [-1, 0, 1]:
                    for dy in [-1, 0, 1]:
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < 16 and 0 <= ny < 16 and self.board[ny][nx] == 9:
                            count += 1
                self.board[y][x] = count

    def draw(self):
        image = Image.new("RGB", (self.width, self.height))
        draw = ImageDraw.Draw(image)

        for y in range(16):
            for x in range(16):
                if self.displayed[y][x]:
                    if self.board[y][x] == 9:
                        image.paste(self.images["boomball"], (x*15, y*15))
                    elif self.board[y][x] == 0:
                        draw.rectangle([x*15, y*15, x*15+14, y*15+14], fill="#808080")
                    else:
                        text = str(self.board[y][x])
                        bbox = draw.textbbox((0, 0), text, font=self.font)
                        w, h = bbox[2]-bbox[0], bbox[3]-bbox[1]
                        draw.rectangle([x*15, y*15, x*15+14, y*15+14], fill="#808080")
                        draw.text(((x*15)+((15-w)/2), (y*15)+((15-h)/2)), text, font=self.font, fill="#FFFFFF")
                   
                elif self.flags[y][x]:
                    image.paste(self.images["flag"], (x*15, y*15))

                draw.rectangle([x*15, y*15, x*15+14, y*15+14], outline="#808080")

        draw.rectangle([self.cursor[0]*15, self.cursor[1]*15, self.cursor[0]*15+14, self.cursor[1]*15+14], outline="#FF0000")

        self.disp.image(image)

    def open(self, x, y):
        if self.displayed[y][x] or self.flags[y][x]:
            return
        self.displayed[y][x] = 1
        if self.board[y][x] == 0:
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < 16 and 0 <= ny < 16:
                        self.open(nx, ny)
        elif self.board[y][x] == 9:
            for y in range(16):
                for x in range(16):
                    if self.board[y][x] == 9:
                        self.displayed[y][x] = 1
            self.draw()
            time.sleep(2)
            
            self.game_over = True

    def check_clear(self):
        for y in range(16):
            for x in range(16):
                if self.board[y][x] != 9 and not self.displayed[y][x]:
                    return
        self.disp.image(self.images["clear"])
        time.sleep(10000)

    def run(self):
        self.disp.image(self.images["main"])
        while True:
            if self.button_A.value == 0:
                time.sleep(0.5)
                break  # A 버튼이 눌렸을 경우 게임 시작

        # 지뢰찾기 게임 시작
        while not self.game_over:
            command = {'move': False, 'up_pressed': False , 'down_pressed': False, 'left_pressed': False, 'right_pressed': False,
                       'A_pressed': False, 'B_pressed': False}

            if self.button_A.value == 0:
                command['A_pressed'] = True
            if self.button_B.value == 0:
                command['B_pressed'] = True

            if self.button_U.value == 0:
                command['up_pressed'] = True
                command['move'] = True
            if self.button_D.value == 0:
                command['down_pressed'] = True
                command['move'] = True
            if self.button_L.value == 0:
                command['left_pressed'] = True
                command['move'] = True
            if self.button_R.value == 0:
                command['right_pressed'] = True
                command['move'] = True
                
            self.process_command(command)
            self.draw()
            time.sleep(0.1)

        # 게임 오버일 때
        while self.game_over:
            self.disp.image(self.images["failed"])
            
    def process_command(self, command):
        if self.game_over:  # 게임 상태가 종료이면 아무런 명령도 처리하지 않음
            return
        if command['move']:
            self.move(command)
        if command['A_pressed']:
            self.open(self.cursor[0], self.cursor[1])
            self.check_clear()
        if command['B_pressed']:
            self.flags[self.cursor[1]][self.cursor[0]] ^= 1

    def move(self, command):
        if command['move']:
            dx, dy = 0, 0
            if command['up_pressed']:
                dy -= 1
            if command['down_pressed']:
                dy += 1
            if command['left_pressed']:
                dx -= 1
            if command['right_pressed']:
                dx += 1
            nx, ny = self.cursor[0] + dx, self.cursor[1] + dy
            if 0 <= nx < 16 and 0 <= ny < 16:
                self.cursor = [nx, ny]


if __name__ == "__main__":
    game = Game()
    game.run()
