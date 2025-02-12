from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time

import keyboard

import numpy as np


# 1. Chrome 옵션 설정 및 드라이버 생성
chrome_options = Options()
chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
chrome_options.add_experimental_option("useAutomationExtension", False)
chrome_options.add_argument("--disable-blink-features=AutomationControlled")  # 자동화 감지 방지
chrome_options.add_experimental_option("prefs", {"profile.default_content_setting_values.notifications": 2})  # 알림 차단

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

# 2. Boolean 값 설정 (True = 한판 더, False = 대기)
continue_play = True  # True이면 "한판 더!" 버튼 클릭, False이면 대기

# 3. 게임 웹사이트 열기
game_url = "https://sedol.wakttu.kr"
driver.get(game_url)

# 4. 페이지 로딩 대기
time.sleep(3)

# 5. 최초 로딩 화면 감지 & "시작!" 버튼 클릭
try:
    start_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//div[contains(text(), '시작!')]"))
    )
    start_button.click()
    print("게임 시작 버튼 클릭 완료")
except Exception as e:
    print("게임 시작 버튼을 찾을 수 없습니다.", e)
    
# 6. 게임 보드 숫자 데이터 가져오기
def get_game_board():
    
    try:
        # 게임 보드 로딩 대기
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".sc-kfmGjC"))
        )

        cells = cells = driver.find_elements(By.CSS_SELECTOR, ".sc-kfmGjC")  # 게임 보드 셀 선택
        
        game_board = []  # 게임 보드 데이터 저장할 리스트

        for cell in cells:
            text = cell.text.strip()
            value = int(text) if text.isdigit() else 0  # 숫자가 없으면 0 (계돌이)
            game_board.append(value)

        # 18x10 배열로 변환 (보드 크기)
        if len(game_board) == 180:  # 정상적으로 데이터가 수집된 경우만 변환
            return np.array(game_board).reshape(10, 18) # 10x18 배열로 변환
        else:
            print(f"예상된 180개의 데이터가 아닌 {len(game_board)}개만 가져왔음")

    except Exception as e:
        print(" 게임 보드를 가져오는 중 오류 발생:", e)

game_board = get_game_board()  # 게임 보드 데이터 가져오기


def find_combinations(game_board):
    height, width = game_board.shape    # 보드 크기 가져오기
    valid_combinations = []             # 가능한 조합 저장할 리스트

    for y in range(height):
        for x in range(width):
            for length in range(2, width - x + 1):
                if x + length <= width:
                    sub_array = game_board[y, x:x + length]
                    if np.sum(sub_array) == 10:
                        valid_combinations.append((x, y, length, 1))  # 가로 선택
            
            # 세로 탐색
            for length in range(2, height - y + 1):
                if y + length <= height:
                    sub_array = game_board[y:y + length, x]
                    if np.sum(sub_array) == 10:
                        valid_combinations.append((x, y, 1, length))  # 세로 선택
            
            # 사각형 탐색 (직사각형 범위 내 합이 10인지 확인)
            for h in range(1, height - y + 1):  # 세로 크기
                for w in range(2, width - x + 1):  # 가로 크기 (최소 2칸)
                    sub_matrix = game_board[y:y + h, x:x + w]  # 사각형 영역 추출
                    if np.sum(sub_matrix) == 10:
                        valid_combinations.append((x, y, w, h))
                        
    return valid_combinations  # 올바른 조합만 반환

# Selenium으로 특정 영역을 마우스 드래그하여 선택 
def select_area(driver, start_x, start_y, width, height):
    try:
        action = ActionChains(driver)

        # 시작 위치에서 마우스 클릭
        start_cell = driver.find_element(By.XPATH, f"//div[contains(@class, 'sc-kfmGjC')][{start_y * 18 + start_x + 1}]")
        action.move_to_element(start_cell).click_and_hold()

        # 끝 위치까지 드래그
        end_cell = driver.find_element(By.XPATH, f"//div[contains(@class, 'sc-kfmGjC')][{(start_y + height - 1) * 18 + start_x + width}]")
        action.move_to_element(end_cell).release().perform()

        print(f"영역 ({start_x}, {start_y}) → ({start_x + width - 1}, {start_y + height - 1}) 선택 완료")

    except Exception as e:
        print("영역 선택 중 오류 발생:", e)

# 전체 게임 플레이 함수
def play_game(driver):
    global game_board  # 전역 변수 사용
    
    print("play_game() 실행 전 게임 보드 상태:\n", game_board)  # 디버깅용
    
    combinations = find_combinations(game_board)  # 합이 10이 되는 조합 찾기
    
    if not combinations:
        print("가능한 조합이 없습니다. 보드 갱신 필요")
        game_board = get_game_board()  # 게임 보드 데이터 다시 가져오기
        return


    # 🔹 가능한 조합 중 첫 번째 선택
    best_choice = combinations[0]
    start_x, start_y, width, height = best_choice

    # 🔹 선택 영역 실행
    select_area(driver, start_x, start_y, width, height)
    
    game_board = update_game_board(game_board, start_x, start_y, width, height)  # 업데이트된 값 저장
    print("play_game() 실행 후 게임 보드 상태:\n", game_board)  # 디버깅용
    time.sleep(1)  # 1초 대기
    
    
def update_game_board(game_board,start_x, start_y, width, height):
    """ 선택된 영역을 0으로 변환하여 게임 보드를 업데이트 """
    for y in range(start_y, start_y + height):
        for x in range(start_x, start_x + width):
            # 보드 크기 제한 추가 (y는 0~9, x는 0~17까지만 가능)
            if y >= 10 or x >= 18:
                print(f"잘못된 좌표: ({x}, {y}), 보드 크기 초과! 선택 무시")
                continue  # 해당 좌표 무시하고 계속 진행
            
            print(f"게임 보드 [{y}, {x}] 값 {game_board[y, x]} → 0으로 변경")
            game_board[y, x] = 0  # 선택된 숫자를 0으로 변경 / NumPy는 [행, 열] 인덱싱이므로 (y, x) 순서로 인덱싱
            
    return game_board


def handle_game_end(driver, continue_play):
    """ 게임이 종료되었을 때 '한판 더!' 또는 '닫기' 버튼을 클릭하는 함수 """
    while True:
        try:
            # "한판 더!" 또는 "닫기" 버튼 감지
            retry_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//div[contains(text(), '한판 더!')]"))
            )
            close_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//div[contains(text(), '닫기')]"))
            )

            if continue_play:
                retry_button.click()  # "한판 더!" 클릭
                print("'한판 더!' 버튼 클릭 완료. 새 게임 시작!")
            else:
                close_button.click()  # "닫기" 클릭
                print("게임 종료. 자동 플레이 종료.")
                break  # 종료 후 루프 탈출

            time.sleep(3)  # 새 게임 시작 대기
            return  # 함수 종료 후 자동 플레이 다시 시작

        except:
            # 버튼이 없으면 게임 진행 중
            print("게임 진행 중...")
            time.sleep(2)


while True:
    play_game(driver)  # 게임 플레이 실행

    # 'q' 키를 누르면 종료
    if keyboard.is_pressed("q"):
        print("수동 종료: 'q' 키 감지됨. 프로그램을 종료합니다.")
        break

    print("게임이 종료되었습니다. 다음 라운드를 대기 중...")