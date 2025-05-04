from selenium import webdriver
from selenium.webdriver.common.by import By
import time
from dotenv import load_dotenv
import os
import re
import requests
import json
from fastapi import APIRouter
from schema.schema import GetNotice


router = router = APIRouter(
    prefix="/api",
    tags=["api"],
    responses={404: {"description": "Not found"}},
)


@router.post("/get_notice")
async def get_notice(req: GetNotice):
    load_dotenv()

    driver = None
    notices: list = []

    try:
        driver = webdriver.Chrome()
        user = req.userid
        password = req.passward
        email = req.email

        if not user or not password:
            raise ValueError("set USERNAME and PASSWORD in .env")

        driver.get("https://portal.nit.ac.jp/")
        time.sleep(1)

        if len(driver.window_handles) > 1:
            driver.switch_to.window(driver.window_handles[1])
        else:
            print("cannot find the login window")

        username_field = driver.find_element(
            By.XPATH,
            "/html/body/div/div/form/table/tbody/tr[4]/td/table/tbody/tr[3]/td[3]/input",
        )
        username_field.send_keys(user)

        password_field = driver.find_element(
            By.XPATH,
            "/html/body/div/div/form/table/tbody/tr[4]/td/table/tbody/tr[4]/td[3]/input",
        )
        password_field.send_keys(password)

        login_button = driver.find_element(
            By.XPATH,
            "/html/body/div/div/form/table/tbody/tr[4]/td/table/tbody/tr[5]/td[2]/input",
        )
        login_button.click()
        time.sleep(2)

        user_name_with_login_history = driver.find_element(
            By.XPATH,
            "/html/body/div/div/form[1]/div[1]/div/table/tbody/tr[1]/td/div/span",
        )
        username = (
            (
                user_name_with_login_history.text.split(" ")[0]
                + user_name_with_login_history.text.split(" ")[1]
            )
            .replace("\u3000", " ")
            .replace("さん", "")
        )
        print(f"login as {username}")

        notice_link = driver.find_element(
            By.XPATH,
            "/html/body/div/div/form[3]/table[2]/tbody/tr/td[4]/table/tbody/tr/td/div/table/tbody/tr/td/table/tbody/tr[1]/td/table[2]/tbody/tr/td/a/span",
        )
        notice_link.click()
        time.sleep(3)

        notice_base_xpath = "/html/body/div/div/form[3]/table[2]/tbody/tr/td[4]/table/tbody/tr/td/div/table/tbody/tr/td/table/tbody/tr[1]/td/table[1]/tbody"

        notice_rows = driver.find_elements(
            By.XPATH, f"{notice_base_xpath}/tr[@class='rowHeight']"
        )

        if not notice_rows:
            print("cannot find notice table")

        for i, row_element in enumerate(notice_rows):
            status = "既読"
            importance = "通常"
            title = "取得失敗"
            sender = "取得失敗"
            date = "取得失敗"
            is_new = False

            unread_icon = row_element.find_elements(
                By.XPATH, ".//td[1]/img[@src='../../image/open_yet.gif']"
            )
            if unread_icon:
                status = "未読"
            else:
                continue

            important_icon = row_element.find_elements(
                By.XPATH, ".//td[2]/img[@src='../../image/topic.gif']"
            )
            if important_icon:
                importance = "重要"

            title_span = row_element.find_element(By.XPATH, ".//td[3]/a/span")
            title_attr = title_span.get_attribute("title")
            title = title_attr.strip() if title_attr else title_span.text.strip()

            sender_span = row_element.find_element(
                By.XPATH, ".//td[3]/span[@class='from']"
            )
            sender_attr = sender_span.get_attribute("title")
            if sender_attr:
                sender = sender_attr.strip()
            else:
                sender_text = sender_span.text.strip()
                sender = sender_text
                child_span_elements = sender_span.find_elements(
                    By.XPATH, "./span[@class='from']"
                )
                if child_span_elements:
                    child_title = child_span_elements[0].get_attribute("title")
                    if child_title:
                        sender = child_title.strip()

            date_span = row_element.find_element(
                By.XPATH, ".//td[3]/span[@class='insDate']"
            )
            date_text = date_span.text
            date_match = re.search(r"\[(\d{4}/\d{2}/\d{2})\]", date_text)
            if date_match:
                date = date_match.group(1)

            new_icon = row_element.find_elements(
                By.XPATH, ".//td[3]/img[@src='../../image/new.gif']"
            )
            if new_icon:
                is_new = True

            notices.append(
                [
                    str(status).replace("\u3000", " "),
                    str(importance).replace("\u3000", " "),
                    str(title).replace("\u3000", " "),
                    str(sender).replace("\u3000", " "),
                    str(date),
                    str(is_new),
                ]
            )

    finally:
        if driver:
            print("scraping finished")
            driver.quit()

    if notices:
        print(f"\n{len(notices)} datas to send:")
        post_url = os.getenv("POST_URL")
        if not post_url:
            raise ValueError("POST_URL environment variable is not set")

        payload = {"username": username, "notices": notices}

        try:
            response = requests.post(post_url, json=payload, timeout=30)
            response.raise_for_status()

            response_data = response.json()
            print("response from GAS:")
            print(json.dumps(response_data, indent=4, ensure_ascii=False))

            if response_data.get("status") != "success":
                print("something went wrong")

        except requests.exceptions.Timeout:
            print("error: request timed out")

        except requests.exceptions.RequestException as e:
            print(f"error: sending data was failed: {e}")

            if e.response is not None:
                print(f"  status_code: {e.response.status_code}")
                try:
                    print(f"  response: {e.response.text}")
                except Exception as read_err:
                    print(f"  failed to read error-msg: {read_err}")

        except Exception as e:
            print(f"ERROR: {e}")

    else:
        print("there is no new notice")
