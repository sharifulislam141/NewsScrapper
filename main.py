import requests
import re
import csv
import json
from bs4 import BeautifulSoup
from time import sleep

def load_more_data(start, total, all_articles):
    archive_url = "https://www.narayanganjtimes.com/ajax_archive_load_more.php"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:137.0) Gecko/20100101 Firefox/137.0",
        "X-Requested-With": "XMLHttpRequest",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Referer": "https://www.narayanganjtimes.com/archives/",
    }

    data = {
        "action": "showContent",
        "newsCount": start,
        "totalRecord": total,
        "rowperpage": 20,
        "iCategoryID": "0",
        "sDate": "",
        "q": " ORDER BY bc.ContentID",
        "db_content": "bn_content"
    }

    response = requests.post(archive_url, headers=headers, data=data)
    soup = BeautifulSoup(response.content, 'html.parser')
    boxes = soup.select('div.DCategoryListNews.MarginTop20')
    print(f"Loaded {len(boxes)} more articles")
    
    for box in boxes:
        article = extract_summary(box)
        if article:
            details = get_article_details(article['link'])
            article.update(details)
            all_articles.append(article)
            print(f"✅ Fetched article: {article['title']}")


def extract_summary(box):
    try:
        title = box.select_one('.pHead').text.strip()
        publish_date = box.select_one('.pDate').text.strip()
        link = box.select_one('a')['href']
        image = box.select_one('img')['src'] if box.select_one('img') else "No image"
        return {
            "title": title,
            "publish_date": publish_date,
            "link": link,
            "image": image
        }
    except:
        return None


def get_article_details(url):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:137.0) Gecko/20100101 Firefox/137.0"
        }
        article_response = requests.get(url, headers=headers)
        soup = BeautifulSoup(article_response.content, 'html.parser')

        content_div = soup.select_one('#contentDetails')
        full_text = content_div.get_text(strip=True, separator="\n") if content_div else "Content not found"

        category_elem = soup.select_one('.category-name')
        category = category_elem.text.strip() if category_elem else "archives"

        return {
            "full_content": full_text,
            "category": category
        }

    except Exception as e:
        print(f"⚠️ Error fetching details from {url}: {e}")
        return {
            "full_content": "Error fetching content",
            "category": "Unknown"
        }


def save_results(articles):
    print("\n💾 Saving to CSV and JSON files...")
    # Save CSV with UTF-8 encoding
    with open("narayanganj_news.csv", "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=articles[0].keys())
        writer.writeheader()
        writer.writerows(articles)

    # Save JSON
    with open("narayanganj_news.json", "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)

    print("✅ Files saved: narayanganj_news.csv, narayanganj_news.json")


def main():
    url = "https://www.narayanganjtimes.com/archives/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:137.0) Gecko/20100101 Firefox/137.0"
    }

    response = requests.get(url, headers=headers)
    html = response.text

    match = re.search(r"let\s+totalRecord\s*=\s*(\d+);", html)
    total_record = int(match.group(1)) if match else 0
    print(f"📊 Total records available: {total_record}")

    try:
        user_limit = int(input("📥 Enter how many records you want to scrape: ").strip())
    except ValueError:
        print("❌ Invalid input. Please enter a number.")
        return

    if user_limit <= 0:
        print("❌ Please enter a number greater than 0.")
        return

    user_limit = min(user_limit, total_record)
    print(f"🔎 Scraping {user_limit} records...")

    soup = BeautifulSoup(html, 'html.parser')
    boxes = soup.select('div.DCategoryListNews.MarginTop20')

    articles = []
    for i, box in enumerate(boxes[:min(20, user_limit)]):
        article = extract_summary(box)
        if article:
            details = get_article_details(article['link'])
            article.update(details)
            articles.append(article)
            print(f"✅ Fetched article {i+1}: {article['title']}")

    if user_limit > 20:
        for start in range(20, user_limit, 20):
            sleep(1)  # Be polite to the server
            load_more_data(start, total_record, articles)

    save_results(articles)


if __name__ == "__main__":
    main()
