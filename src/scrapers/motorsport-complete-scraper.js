const puppeteer = require('puppeteer');
const { Cluster } = require('puppeteer-cluster');
const fs = require('fs-extra');
const axios = require('axios');

class FixedMotorsportScraper {
    constructor() {
        this.scraped_data = [];
        this.failed_urls = [];
    }

    async setupCluster() {
        console.log('🚀 Setting up Fixed Puppeteer Cluster...');

        this.cluster = await Cluster.launch({
            concurrency: Cluster.CONCURRENCY_CONTEXT,
            maxConcurrency: 4, // Reduced for stability
            timeout: 60000, // Reduced timeout
            puppeteerOptions: {
                headless: true,
                args: [
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage'
                ]
            },
            retryLimit: 2,
            retryDelay: 3000
        });

        await this.cluster.task(async ({ page, data }) => {
            return await this.scrapePage(page, data);
        });
    }

    async scrapePage(page, data) {
        const { url, type, year } = data;

        try {
            console.log(`📄 Scraping ${type} ${year || ''}: ${url}`);

            await page.goto(url, {
                waitUntil: 'domcontentloaded', // More reliable than networkidle2
                timeout: 30000
            });

            // Use setTimeout instead of waitForTimeout
            await new Promise(resolve => setTimeout(resolve, 1000));

            const extracted_data = await page.evaluate((url, type, year) => {
                const articles = [];

                // Multiple selector strategies
                const selectors = [
                    'article',
                    '[class*="news"]',
                    '[class*="listing"]',
                    'h1, h2, h3',
                    'a[href*="/f1/"]'
                ];

                for (const selector of selectors) {
                    const elements = document.querySelectorAll(selector);

                    if (elements.length > 0) {
                        elements.forEach((element, index) => {
                            if (index < 20) { // Limit per page
                                try {
                                    const title = element.innerText?.trim() ||
                                                element.textContent?.trim() || '';

                                    if (title && title.length > 10) {
                                        const link = element.href ||
                                                    element.querySelector('a')?.href ||
                                                    url;

                                        articles.push({
                                            title: title.substring(0, 200), // Limit title length
                                            content: title.substring(0, 500),
                                            url: link,
                                            type: type,
                                            year: year,
                                            source: 'Motorsport.com Fixed',
                                            scraped_at: new Date().toISOString()
                                        });
                                    }
                                } catch (e) {
                                    // Skip problematic elements
                                }
                            }
                        });

                        if (articles.length > 0) break; // Found articles, stop trying selectors
                    }
                }

                return articles;
            }, url, type, year);

            if (extracted_data && extracted_data.length > 0) {
                this.scraped_data.push(...extracted_data);
                console.log(`✅ Extracted ${extracted_data.length} items from ${url}`);
            }

            return extracted_data;

        } catch (error) {
            console.log(`❌ Error scraping ${url}: ${error.message}`);
            this.failed_urls.push(data);
            return [];
        }
    }

    generateUrls() {
        const urls = [];
        const base_routes = {
            news: 'https://www.motorsport.com/f1/news',
            results: 'https://www.motorsport.com/f1/results',
            standings: 'https://www.motorsport.com/f1/standings'
        };
        const years = [2023, 2024, 2025]; // Focus on recent years for faster testing

        for (const [route_type, base_url] of Object.entries(base_routes)) {
            for (const year of years) {
                urls.push({
                    url: `${base_url}/${year}`,
                    type: route_type,
                    year: year
                });
            }
        }

        return urls;
    }

    async scrapeAll() {
        console.log('🏎️ Starting Fixed Motorsport Scraping...');

        await this.setupCluster();

        const all_urls = this.generateUrls();
        console.log(`📋 Generated ${all_urls.length} URLs to scrape`);

        for (const url_data of all_urls) {
            this.cluster.queue(url_data);
        }

        await this.cluster.idle();
        await this.cluster.close();

        console.log(`🎉 Fixed scraping completed!`);
        console.log(`✅ Successfully scraped: ${this.scraped_data.length} articles`);
        console.log(`❌ Failed URLs: ${this.failed_urls.length}`);

        // Save data
        await fs.writeJson('./fixed_motorsport_data.json', {
            scraped_at: new Date().toISOString(),
            total_articles: this.scraped_data.length,
            data: this.scraped_data
        }, { spaces: 2 });

        console.log(`💾 Saved ${this.scraped_data.length} articles to fixed_motorsport_data.json`);

        // Send to Python backend
        try {
            const response = await axios.post('http://localhost:5000/admin/bulk-add-data', {
                articles: this.scraped_data
            });
            console.log('✅ Data sent to Python successfully');
        } catch (error) {
            console.log('❌ Failed to send to Python, but data saved locally');
        }
    }
}

// Run the fixed scraper
async function main() {
    const scraper = new FixedMotorsportScraper();
    await scraper.scrapeAll();
}

main().catch(console.error);
