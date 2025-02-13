import game_driver
import game_logic
import time

# Chrome 드라이버 실행
driver = game_driver.setup_driver()
game_url = "https://sedol.wakttu.kr"
driver.get(game_url)

# 게임 시작 버튼 클릭
try:
    start_button = game_logic.WebDriverWait(driver, 10).until(
        game_logic.EC.element_to_be_clickable((game_logic.By.XPATH, "//div[contains(text(), '시작!')]"))
    )
    time.sleep(1)
    start_button.click()
    print("게임 시작 버튼 클릭 완료")
except Exception as e:
    print("게임 시작 버튼을 찾을 수 없습니다.", e)

game_board = None

# 게임 자동 플레이 루프
while True:
    try:
        # 창이 열려 있는지 확인
        if not driver.window_handles:
            print("게임 창이 닫혔습니다. 프로그램을 종료합니다.")
            break
        
        if game_logic.get_game_timer(driver) == "0":
            time.sleep(10)
            print("게임 종료. 새 게임 시작")
            game_board = None
            game_logic.handle_game_end(driver, continue_play=True)
        if game_board is None:
            game_board = game_logic.get_game_board(driver)
            if game_board is None:
                print("게임 보드를 불러올 수 없음, 다시 시도")
                continue

        combinations = game_logic.find_combinations(game_board)
        if not combinations:
            # print("가능한 조합 없음")
            game_board = game_logic.get_game_board(driver)  # 게임 보드 갱신
            time.sleep(1)
            continue

        best_choice = combinations[0]
        x, y, w, h = best_choice
        game_board[y:y + h, x:x + w] = 0 # 선택한 영역을 0으로 초기화
        game_logic.select_area(driver, *best_choice)
        time.sleep(1)
            
    except Exception as e:
        print("오류 발생 또는 창이 닫힘:", e)
        break

# 프로그램 종료
try:
    driver.quit()
except:
    pass
