import numpy as np
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import time

def get_game_board(driver):
    """게임 보드의 숫자 데이터를 가져와서 2D 배열로 변환"""
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".sc-kfmGjC"))
        )
        cells = driver.find_elements(By.CSS_SELECTOR, ".sc-kfmGjC")

        game_board = []
        for cell in cells:
            text = cell.text.strip()
            value = int(text) if text.isdigit() else 0
            game_board.append(value)

        if len(game_board) == 180:  # 18x10 배열로 변환
            return np.array(game_board).reshape(10, 18)
        else:
            print(f"데이터 오류: 예상 180개 -> 실제 {len(game_board)}개")

    except Exception as e:
        print("게임 보드를 가져오는 중 오류 발생:", e)

def find_combinations(game_board):
    """합이 10이 되는 조합을 찾음"""
    height, width = game_board.shape
    valid_combinations = []
                    
    for y in range(height):
        for x in range(width):
            # 가로 탐색
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
            
            # 사각형 탐색 (사각형 범위 내 합이 10인지 확인)
            for h in range(1, height - y + 1): 			# 세로 크기
                for w in range(2, width - x + 1):  		# 가로 크기 (최소 2칸)
                    sub_matrix = game_board[y:y + h, x:x + w]  # 사각형 영역 추출
                    if np.sum(sub_matrix) == 10:
                        valid_combinations.append((x, y, w, h))

    return valid_combinations

def select_area(driver, start_x, start_y, width, height):
    """마우스를 사용해 특정 영역을 드래그하여 선택"""
    try:
        action = ActionChains(driver)
        start_cell = driver.find_element(By.XPATH, f"//div[contains(@class, 'sc-kfmGjC')][{start_y * 18 + start_x + 1}]")
        action.move_to_element(start_cell).click_and_hold()

        end_cell = driver.find_element(By.XPATH, f"//div[contains(@class, 'sc-kfmGjC')][{(start_y + height - 1) * 18 + start_x + width}]")
        action.move_to_element(end_cell).release().perform()

        # print(f"영역 선택 완료: ({start_x}, {start_y}) → ({start_x + width - 1}, {start_y + height - 1})")

    except Exception as e:
        print("영역 선택 중 오류 발생:", e)
        
def get_game_timer(driver):
    """게임 타이머의 시간 가져오기"""
    try:
        timer = driver.find_element(By.CSS_SELECTOR, ".sc-kuACkN")
        return timer.text

    except:
        return "0"

def handle_game_end(driver, continue_play):
    """한 판이 끝나면 '한판 더!' 또는 '닫기' 버튼을 클릭"""
    
    retry_button = WebDriverWait(driver, 5).until(
        EC.element_to_be_clickable((By.XPATH, "//div[contains(text(), '한판 더!')]"))
    )
    close_button = WebDriverWait(driver, 5).until(
        EC.element_to_be_clickable((By.XPATH, "//div[contains(text(), '닫기')]"))
    )
    
    # 버튼이 존재하지 않을 경우 return
    if not retry_button or not close_button:
        return

    if continue_play:
        retry_button.click()  # "한판 더!" 클릭
        print("'한판 더!' 버튼 클릭 완료. 새 게임 시작!")
    else:
        close_button.click()  # "닫기" 클릭
        print("게임 종료. 자동 플레이 종료.")