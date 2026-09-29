#!/usr/bin/env python3
"""
Universal Web Scraping Suite - Unified CLI
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Run individual scrapers, export datasets, or execute full end-to-end multi-target scraping.
"""

import sys
import argparse
import json
from pathlib import Path
from scrapers import (
    CompanyScraper,
    RestaurantScraper,
    GameScraper,
    WikipediaScraper,
    EcommerceScraper,
    InternshipScraper,
)
from scrapers.core.storage import DataStorage


def print_banner():
    banner = """
================================================================================
    🌐 UNIVERSAL WEB SCRAPING INTELLIGENCE SUITE
    📦 Modular • 🛡️ Resilient • ⚡ Async-Ready • 💾 Multi-Format Export
================================================================================
    """
    print(banner)


def handle_company(args, storage: DataStorage):
    scraper = CompanyScraper()
    print(f"\n[🏢 COMPANY SCRAPER] Analyzing: {args.name} (Jobs Query: {args.query})...")
    
    if args.full_dossier:
        dossier = scraper.build_company_dossier(args.name)
        json_path = storage.save_json(dossier, f"company_{args.name.lower()}.json")
        print(f"✅ Full Dossier Generated for '{args.name}'")
        print(f"   Tech Stack: {', '.join(dossier.get('tech_stack', [])[:6])}...")
        print(f"   Headquarters: {dossier.get('headquarters')}")
        print(f"   Open Jobs Count: {dossier.get('job_openings_count')}")
        print(f"   📁 Saved to: {json_path}")
    else:
        jobs = scraper.scrape_company_jobs(query=args.query, limit=args.limit)
        json_path = storage.save_json(jobs, f"company_jobs_{args.query}.json")
        csv_path = storage.save_csv(jobs, f"company_jobs_{args.query}.csv")
        print(f"✅ Found {len(jobs)} tech job postings for '{args.query}'")
        for j in jobs[:3]:
            print(f"   - {j['company_name']} | {j['position']} | {j['salary_range']}")
        print(f"   📁 JSON Saved: {json_path}")
        print(f"   📁 CSV Saved:  {csv_path}")


def handle_restaurant(args, storage: DataStorage):
    scraper = RestaurantScraper()
    print(f"\n[🍽️ RESTAURANT SCRAPER] Location: {args.city} | Cuisine: {args.cuisine}...")
    
    if args.menu_details:
        details = scraper.scrape_restaurant_details(args.cuisine, city=args.city)
        json_path = storage.save_json(details, f"restaurant_{args.cuisine.lower().replace(' ', '_')}.json")
        print(f"✅ Deep Details Scraped for '{details['name']}' ({details['rating']} ★ - {details['price_tier']})")
        print(f"   Address: {details['address']}")
        print(f"   Phone: {details['phone']}")
        print("   Sample Menu:")
        for item in details.get("menu_items", [])[:3]:
            print(f"     • {item['name']} - ${item['price']:.2f} ({item['category']})")
        print(f"   📁 Saved to: {json_path}")
    else:
        restaurants = scraper.search_restaurants(city=args.city, cuisine=args.cuisine, limit=args.limit)
        json_path = storage.save_json(restaurants, f"restaurants_{args.city[:8]}_{args.cuisine}.json")
        csv_path = storage.save_csv(restaurants, f"restaurants_{args.city[:8]}_{args.cuisine}.csv")
        print(f"✅ Found {len(restaurants)} restaurants:")
        for r in restaurants[:4]:
            print(f"   - {r['name']} | Rating: {r['rating']} ★ | Tier: {r['price_tier']} | Tel: {r['phone']}")
        print(f"   📁 JSON Saved: {json_path}")
        print(f"   📁 CSV Saved:  {csv_path}")


def handle_game(args, storage: DataStorage):
    scraper = GameScraper()
    print(f"\n[🎮 GAME SCRAPER] Query: {args.search}...")
    
    if args.app_id:
        details = scraper.scrape_game_details(args.app_id)
        json_path = storage.save_json(details, f"game_{details['title'].lower().replace(' ', '_')}.json")
        print(f"✅ Steam Intelligence Extracted for: '{details['title']}'")
        print(f"   Price: {details['price'].get('formatted')} | Metacritic: {details.get('metacritic_score')}/100")
        print(f"   Genres: {', '.join(details.get('genres', []))}")
        print(f"   Platforms: {', '.join(details.get('platforms', []))}")
        print(f"   📁 Saved to: {json_path}")
    elif args.free_games:
        free_games = scraper.scrape_top_free_games(category=args.search, limit=args.limit)
        json_path = storage.save_json(free_games, f"free_games_{args.search}.json")
        csv_path = storage.save_csv(free_games, f"free_games_{args.search}.csv")
        print(f"✅ Scraped {len(free_games)} Free-to-Play Games in '{args.search}':")
        for g in free_games[:3]:
            print(f"   - {g['title']} | Genre: {g['genre']} | Platform: {g['platform']}")
        print(f"   📁 JSON Saved: {json_path}")
        print(f"   📁 CSV Saved:  {csv_path}")
    else:
        games = scraper.search_steam_games(query=args.search, limit=args.limit)
        json_path = storage.save_json(games, f"steam_search_{args.search}.json")
        csv_path = storage.save_csv(games, f"steam_search_{args.search}.csv")
        print(f"✅ Found {len(games)} Steam titles for '{args.search}':")
        for g in games[:4]:
            print(f"   - {g['title']} (AppID: {g['app_id']}) | Price: {g['price']['formatted']} | Reviews: {g['user_reviews'][:30]}...")
        print(f"   📁 JSON Saved: {json_path}")
        print(f"   📁 CSV Saved:  {csv_path}")


def handle_wiki(args, storage: DataStorage):
    scraper = WikipediaScraper(language=args.lang)
    print(f"\n[📖 WIKIPEDIA SCRAPER] Topic: {args.topic} (Lang: {args.lang})...")
    
    if args.random:
        article = scraper.get_random_article()
    else:
        article = scraper.scrape_article(args.topic)
        
    json_path = storage.save_json(article, f"wiki_{article['title'].lower().replace(' ', '_')}.json")
    print(f"✅ Wikipedia Article Scraped: '{article['title']}'")
    print(f"   URL: {article['url']}")
    print(f"   Infobox Keys: {list(article.get('infobox', {}).keys())[:5]}")
    print(f"   Sections Count: {len(article.get('sections', []))}")
    print(f"   Tables Extracted: {len(article.get('tables', []))}")
    print(f"   Summary Preview: {article['summary'][:200]}...")
    print(f"   📁 Saved to: {json_path}")


def handle_ecommerce(args, storage: DataStorage):
    scraper = EcommerceScraper()
    print(f"\n[🛍️ E-COMMERCE SCRAPER] Category: {args.category} (Pages: {args.pages})...")
    
    products = scraper.scrape_category_products(category_name=args.category, max_pages=args.pages)
    json_path = storage.save_json(products, f"ecommerce_{args.category.lower().replace(' ', '_')}.json")
    csv_path = storage.save_csv(products, f"ecommerce_{args.category.lower().replace(' ', '_')}.csv")
    
    print(f"✅ Scraped {len(products)} products in '{args.category}':")
    for p in products[:4]:
        print(f"   - {p['title'][:35]}... | Price: {p['price']['formatted']} | Rating: {p['rating']} ★ | {p['availability']}")
    print(f"   📁 JSON Saved: {json_path}")
    print(f"   📁 CSV Saved:  {csv_path}")


def handle_internships(args, storage: DataStorage):
    scraper = InternshipScraper()
    print(f"\n[🎓 TECH INTERNSHIP SCRAPER - BATCH 2028] Filter: Category='{args.category}', Search='{args.search}', Location='{args.location}'...")
    
    if args.export:
        res = scraper.export_all()
        print(f"✅ Full 2028 Tech Internships Dataset Exported successfully!")
        print(f"   Total Companies: {res['total_companies']}")
        print(f"   📁 JSON Export:   {res['json_path']}")
        print(f"   📁 CSV Export:    {res['csv_path']}")
        print(f"   🗄️ SQLite DB:     {res['db_path']}")
    else:
        results = scraper.filter_internships(
            category=args.category if args.category != "all" else None,
            role=args.role,
            location=args.location,
            search=args.search,
        )
        print(f"✅ Found {len(results)} matching hiring companies for Batch 2028:")
        for c in results[:6]:
            print(f"   • {c['company_name']} ({c['category']}) | Stipend: {c['stipend_range']}")
            print(f"     Roles: {', '.join(c['roles_offered'][:3])}")
            print(f"     Careers Portal: {c['careers_url']}")
        if len(results) > 6:
            print(f"   ... and {len(results) - 6} more companies. (Run with --export to save full dataset to CSV/JSON/SQLite)")


def run_demo_all():
    print_banner()
    print("🚀 Executing Full Multi-Target Scraping Demonstration across all 5 domains...\n")
    storage = DataStorage()
    
    # 1. Company
    print("--------------------------------------------------------------------------------")
    print("1️⃣ Scraping Tech Company Dossier (Stripe)...")
    c_scraper = CompanyScraper()
    dossier = c_scraper.build_company_dossier("Stripe")
    storage.save_json(dossier, "demo_company_stripe.json")
    print(f"   -> Extracted {len(dossier.get('tech_stack', []))} technologies and {dossier.get('job_openings_count')} jobs.")
    
    # 2. Restaurant
    print("\n--------------------------------------------------------------------------------")
    print("2️⃣ Scraping Restaurant & Menu Intelligence (New York, Italian)...")
    r_scraper = RestaurantScraper()
    r_details = r_scraper.scrape_restaurant_details("Bella Trattoria", city="New York, NY")
    storage.save_json(r_details, "demo_restaurant_bella.json")
    print(f"   -> Extracted {len(r_details.get('menu_items', []))} menu items with pricing & diet tags.")
    
    # 3. Games
    print("\n--------------------------------------------------------------------------------")
    print("3️⃣ Scraping Steam Storefront & Game Intelligence (Cyberpunk 2077)...")
    g_scraper = GameScraper()
    g_details = g_scraper.scrape_game_details("1091500")
    storage.save_json(g_details, "demo_game_cyberpunk.json")
    print(f"   -> Extracted Metacritic {g_details.get('metacritic_score')}, Specs, Genres, and Pricing.")
    
    # 4. Wikipedia
    print("\n--------------------------------------------------------------------------------")
    print("4️⃣ Scraping Deep Wikipedia Knowledge (Artificial Intelligence)...")
    w_scraper = WikipediaScraper()
    w_article = w_scraper.scrape_article("Artificial_intelligence")
    storage.save_json(w_article, "demo_wiki_ai.json")
    print(f"   -> Extracted Infobox, {len(w_article.get('sections', []))} sections, and {len(w_article.get('tables', []))} tables.")
    
    # 5. E-Commerce
    print("\n--------------------------------------------------------------------------------")
    print("5️⃣ Scraping E-Commerce Product Catalog (Science Fiction)...")
    e_scraper = EcommerceScraper()
    e_products = e_scraper.scrape_category_products(category_name="Science Fiction", max_pages=1)
    storage.save_json(e_products, "demo_ecommerce_scifi.json")
    storage.save_csv(e_products, "demo_ecommerce_scifi.csv")
    print(f"   -> Extracted {len(e_products)} products with prices, ratings, and stock status.")
    
    print("\n================================================================================")
    print(f"🎉 ALL 5 SCRAPERS EXECUTED SUCCESSFULLY!")
    print(f"📁 Output files and SQLite Database saved in: {storage.output_dir.resolve()}")
    print(f"🗄️ SQLite Database: {storage.db_path.resolve()}")
    print("================================================================================\n")


def interactive_menu():
    print_banner()
    storage = DataStorage()
    
    while True:
        print("\nSelect a Scraper to Run:")
        print("  [1] 🏢 Company & Tech Stack Scraper")
        print("  [2] 🍽️ Restaurant & Menu Scraper")
        print("  [3] 🎮 Video Game & Steam Scraper")
        print("  [4] 📖 Wikipedia Deep Knowledge Scraper")
        print("  [5] 🛍️ E-Commerce & Product Catalog Scraper")
        print("  [6] 🎓 Batch 2028 Tech Internships Intelligence (365+ Companies)")
        print("  [7] 🚀 Run All Scrapers (Full Demo)")
        print("  [8] 🗄️ Inspect SQLite Database Records")
        print("  [0] 🚪 Exit")
        
        choice = input("\nEnter choice [0-8]: ").strip()
        
        if choice == "1":
            comp = input("Enter company name (default: Stripe): ").strip() or "Stripe"
            dossier = CompanyScraper().build_company_dossier(comp)
            path = storage.save_json(dossier, f"company_{comp.lower()}.json")
            print(f"\n✅ Dossier generated and saved to {path}!")
            
        elif choice == "2":
            city = input("Enter city (default: New York, NY): ").strip() or "New York, NY"
            cuisine = input("Enter cuisine or restaurant name (default: Italian): ").strip() or "Italian"
            details = RestaurantScraper().scrape_restaurant_details(cuisine, city=city)
            path = storage.save_json(details, f"restaurant_{cuisine.lower()}.json")
            print(f"\n✅ Restaurant details and menu saved to {path}!")
            
        elif choice == "3":
            query = input("Enter game title or Steam App ID (default: Cyberpunk 2077): ").strip() or "Cyberpunk 2077"
            game = GameScraper().scrape_game_details(query)
            path = storage.save_json(game, f"game_{game['title'].lower().replace(' ', '_')}.json")
            print(f"\n✅ Game specs and ratings saved to {path}!")
            
        elif choice == "4":
            topic = input("Enter Wikipedia topic (default: Web scraping): ").strip() or "Web scraping"
            article = WikipediaScraper().scrape_article(topic)
            path = storage.save_json(article, f"wiki_{article['title'].lower().replace(' ', '_')}.json")
            print(f"\n✅ Wikipedia article and infobox saved to {path}!")
            
        elif choice == "5":
            cat = input("Enter category (default: Science Fiction): ").strip() or "Science Fiction"
            prods = EcommerceScraper().scrape_category_products(cat, max_pages=1)
            path = storage.save_json(prods, f"ecommerce_{cat.lower().replace(' ', '_')}.json")
            print(f"\n✅ Scraped {len(prods)} products to {path}!")
            
        elif choice == "6":
            iscraper = InternshipScraper()
            res = iscraper.export_all()
            print(f"\n✅ Exported {res['total_companies']} Batch 2028 Tech Hiring Companies to:")
            print(f"   📁 JSON: {res['json_path']}")
            print(f"   📁 CSV:  {res['csv_path']}")
            print(f"   🗄️ DB:   {res['db_path']}")
            
        elif choice == "7":
            run_demo_all()
            
        elif choice == "8":
            print("\n🗄️ Querying SQLite Database Summary:")
            for table in ["companies", "restaurants", "games", "wikipedia_articles", "ecommerce_products", "internships_2028"]:
                try:
                    df = storage.query_db(f"SELECT COUNT(*) as count FROM {table}")
                    cnt = df["count"].iloc[0]
                    print(f"   • Table '{table}': {cnt} records")
                except Exception as e:
                    print(f"   • Table '{table}': not initialized yet ({e})")
                    
        elif choice in ["0", "q", "exit"]:
            print("\nGoodbye! Happy scraping! 🌐\n")
            break
        else:
            print("Invalid option. Please try again.")


def main():
    parser = argparse.ArgumentParser(
        description="Universal Web Scraping Intelligence Suite",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    parser.add_argument("--demo-all", action="store_true", help="Run automated test/demo of all scrapers")
    parser.add_argument("--interactive", "-i", action="store_true", help="Launch interactive CLI menu")
    
    subparsers = parser.add_subparsers(dest="command", help="Available scraping subcommands")
    
    # 1. Company Subcommand
    comp_parser = subparsers.add_parser("company", help="Scrape company intelligence & tech jobs")
    comp_parser.add_argument("--name", "-n", default="Stripe", help="Company name (e.g. 'Stripe', 'Google')")
    comp_parser.add_argument("--query", "-q", default="python", help="Tech job search query (e.g. 'python', 'react')")
    comp_parser.add_argument("--limit", "-l", type=int, default=10, help="Max results limit")
    comp_parser.add_argument("--full-dossier", "-d", action="store_true", help="Build full multi-source dossier")
    
    # 2. Restaurant Subcommand
    rest_parser = subparsers.add_parser("restaurant", help="Scrape restaurant directories & menus")
    rest_parser.add_argument("--city", "-c", default="New York, NY", help="City and State")
    rest_parser.add_argument("--cuisine", default="Italian", help="Cuisine type or restaurant name")
    rest_parser.add_argument("--limit", "-l", type=int, default=10, help="Max listings limit")
    rest_parser.add_argument("--menu-details", "-m", action="store_true", help="Scrape full menu and details")
    
    # 3. Game Subcommand
    game_parser = subparsers.add_parser("game", help="Scrape Steam game details & free games")
    game_parser.add_argument("--search", "-s", default="Cyberpunk 2077", help="Search game title or category")
    game_parser.add_argument("--app-id", "-a", help="Steam Numerical App ID (e.g. 1091500)")
    game_parser.add_argument("--limit", "-l", type=int, default=10, help="Max results limit")
    game_parser.add_argument("--free-games", "-f", action="store_true", help="Scrape Free-to-Play games catalog")
    
    # 4. Wikipedia Subcommand
    wiki_parser = subparsers.add_parser("wiki", help="Scrape Wikipedia deep articles, infoboxes, & tables")
    wiki_parser.add_argument("--topic", "-t", default="Artificial_intelligence", help="Wikipedia topic or page title")
    wiki_parser.add_argument("--lang", default="en", help="Language edition (e.g. 'en', 'fr', 'de', 'es')")
    wiki_parser.add_argument("--random", "-r", action="store_true", help="Scrape a random Wikipedia article")
    
    # 5. E-Commerce Subcommand
    ecom_parser = subparsers.add_parser("ecommerce", help="Scrape e-commerce product catalogs & prices")
    ecom_parser.add_argument("--category", "-c", default="Science Fiction", help="Product category")
    ecom_parser.add_argument("--pages", "-p", type=int, default=1, help="Number of pagination pages")
    
    # 6. Internships Subcommand (Batch 2028 Tech Internships)
    intern_parser = subparsers.add_parser("internships", help="Scrape Batch 2028 B.Tech software & tech internships (365+ companies)")
    intern_parser.add_argument("--category", "-c", default="all", help="Category filter (e.g. 'faang', 'hft', 'unicorn', 'ai', 'saas', 'embedded')")
    intern_parser.add_argument("--role", "-r", default=None, help="Role filter (e.g. 'SDE', 'AI', 'Full Stack', 'DevOps', 'Cybersecurity')")
    intern_parser.add_argument("--location", "-loc", default=None, help="Location filter (e.g. 'Bangalore', 'Hyderabad', 'Pune', 'Gurgaon', 'Remote')")
    intern_parser.add_argument("--search", "-s", default=None, help="Search company name or tech keyword")
    intern_parser.add_argument("--export", "-e", action="store_true", help="Export full 365+ company dataset to CSV, JSON, and SQLite")
    
    args = parser.parse_args()
    storage = DataStorage()
    
    if args.demo_all:
        run_demo_all()
    elif args.interactive or len(sys.argv) == 1:
        interactive_menu()
    elif args.command == "company":
        handle_company(args, storage)
    elif args.command == "restaurant":
        handle_restaurant(args, storage)
    elif args.command == "game":
        handle_game(args, storage)
    elif args.command == "wiki":
        handle_wiki(args, storage)
    elif args.command == "ecommerce":
        handle_ecommerce(args, storage)
    elif args.command == "internships":
        handle_internships(args, storage)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
