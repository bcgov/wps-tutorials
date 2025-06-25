# 🔥🌦️ Wildfire Weather Data Extractor

> Transform your wildfire data into a weather-enriched powerhouse! 🚀

[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Google Earth Engine](https://img.shields.io/badge/Google_Earth_Engine-Enabled-green.svg)](https://earthengine.google.com/)
[![Made with ❤️](https://img.shields.io/badge/Made%20with-❤️-red.svg)](https://github.com/bcgov/wps-labs)

## 🎯 What Does This Script Do?

Ever wondered what the weather was like when those wildfires ignited? This script takes your wildfire location data and enriches it with **real-time historical weather information** from Google Earth Engine's ERA5 dataset! 

### 🌟 Key Features

- 🌡️ **Temperature data** (in Celsius) - Know exactly how hot it was!
- 💨 **Wind speed & direction** (in meters/second) - Critical for understanding fire spread
- 💧 **Humidity levels** - Dewpoint temperature for moisture analysis
- 🌍 **Soil temperature** - Ground-level environmental conditions
- 📊 **Batch processing** - Handle massive datasets without breaking a sweat
- 🔄 **Smart retry logic** - Because APIs can be moody sometimes
- 📁 **Multiple data formats** - CSV, Excel, JSON, SQLite - we got you covered!
- 💾 **Auto-save progress** - Never lose your precious computations

## 💡 What Problem Does This Solve

- **Fire researchers** need weather context for wildfire analysis
- **Insurance companies** want to understand fire risk factors
- **Emergency planners** need historical weather patterns for fire-prone areas
- **Data scientists** want to build predictive models with rich feature sets


## 📋 Prerequisites

Before we dive in, make sure you have:
- 🐍 **Python 3.8+** installed
- ☁️ **Google Cloud Project** with Earth Engine API enabled
- 💻 Basic knowledge of Python and pandas

### 🛠️ Installation

1. **Clone this awesome repository** 📂
```bash
git clone https://github.com/bcgov/wps-tutorials.git
cd data/historical_bc_wildfires
```

2. **Install the magic dependencies** ✨
```bash
pip install -r requirements.txt
```

3. **Configure your environment** 🔧

If you don't already have a `.env` file in your repository,  create one using the following commands:
```bash
touch .env
start .env
```

If you needed help creating a Google Earth Engine project, lucky for you I've published a [**tutorial**](https://medium.com/towards-artificial-intelligence/how-to-set-up-a-google-earth-engine-cloud-project-fe5472ddbaeb) on exactly how to do so. See you on the other side!

Once you have a Google Earth Engine project name in place, edit the `.env` file and add your Google Earth Engine project name in it:
```bash
PROJECT_NAME="insert-your-project-name"
```

Last but certainly not least, we need to add a `.gitignore` file to our repository using the following commands we saw earlier in the event that we don't already have one:

```bash
touch .gitignore
start .gitignore
```

The `.gitignore` file acts as a security guard for your repository, preventing Git from tracking, uploading, and displaying sensitive information when you commit code to version control platforms like GitHub. Adding files like `.env` to `.gitignore` is crucial because these files contain sensitive information like your Google Cloud project name, API keys, passwords, and other configuration secrets that should never be publicly visible. Without proper `.gitignore` protection, you could accidentally expose your project credentials to anyone who views your repository, potentially leading to unauthorized access to your Google Earth Engine resources or unexpected billing charges.

If you're curious as to what a `.gitignore` file looks like or how it should be structured, feel free to [**check out the template**](https://github.com/bcgov/wps-tutorials/blob/main/.gitignore) we used for this project.

### 📊 Required Data Format

Your input data should contain some form of these essential columns:

| Column Name | Description | Example |
|-------------|-------------|---------|
| `LATITUDE` | Fire location latitude | `45.123456` |
| `LONGITUDE` | Fire location longitude | `-120.654321` |
| `FIRE_LABEL` | Unique fire ID value | `FIRE_2023_001` |
| `DATE_COLUMN` | Date/time column | `20230515` or `20230515143000` |

**📅 Supported Date Formats for the `DATE_COLUMN`:**
- `YYYYMMDD` (e.g., `20230515`)
- `YYYYMMDDHHMMSS` (e.g., `20230515143000`)

**📁 Supported File Formats:**
- 📄 CSV files (`.csv`)
- 📊 Excel files (`.xlsx`, `.xls`)
- 📋 JSON files (`.json`)
- 🗄️ SQLite databases (`.db`)
- 🌐 Remote URLs for any of the above!


## 🏃‍♂️ Basic Usage

Simply run the script in the command line terminal:

```bash
python extract.py
```

Then follow the prompts the script provides which will include the following:
1. 🤖 Ask you to provide your data source (file path or URL)
2. 📅 Ask for your date column name

The script will then proceed to execute the following actions:
- 🔍 Process your data in smart batches
- 💾 Save results automatically to your Downloads folder
- 🎉 Celebrate your enriched dataset!

### Sample Output

Your enriched dataset will include all original columns PLUS:

```csv
fire_label,ignition_datetime,temperature_c,wind_speed_ms,wind_direction_deg,wind_direction,humidity_dewpoint_temperature_2m,soil_temperature_level_1
FIRE_2023_001,2023-05-15 14:30:00,25.7,4.2,245.8,Southwest,12.3,28.1
```


## ⚙️ Advanced Configuration

Want more control? You can add the following customizations:

**Batch Size** (default: 100)
- Larger batches = faster processing
- Smaller batches = more stable for large datasets

**Batch Delay** (default: 3 seconds)
- Prevents API rate limiting
- Adjust based on your quota limits

### 🔧 Configuration Options


Add the following enrichments to your `.env` file with:

```bash
# Required: Your Google Earth Engine project name
PROJECT_NAME="insert-your-project-name"

# Optional: Processing parameters
BATCH_SIZE=100
BATCH_DELAY=3
MAX_RETRIES=3
```

### 📈 Performance Tips

#### Optimize Your Processing

- **🎯 Batch Size**: Start with 50-100 rows per batch
- **⏱️ Batch Delay**: 3-5 seconds works well for most quotas
- **📊 Data Prep**: Clean your coordinates and dates first
- **💾 Resume Feature**: Individual batch files let you resume if interrupted

### Memory Management

- The script processes data in chunks to avoid memory issues
- Each batch is saved automatically - no data loss!
- Monitor your Google Earth Engine quota usage

## 🐛 Troubleshooting

### Common Issues & Solutions

**📊 "No data available" errors**
- Check your date formats (use supported formats)
- Verify coordinates are valid (lat: -90 to 90, lon: -180 to 180)
- Some locations/dates might not have ERA5 coverage

**🚫 Permission Denied errors**
- Ensure your Google Cloud project has Earth Engine API enabled
- Check your project name in the `.env` file

**💾 File saving issues**
- Script auto-creates directories
- Check disk space in your Downloads folder

## 🤝 Contributing

Found a bug? Have an awesome feature idea?

1. Fork this repository 🍴
2. Create your feature branch 🌟
3. Commit your changes 💾
4. Push to the branch 🚀
5. Open a Pull Request 📬

## 📜 License

This project is licensed under the **Apache License 2.0** - see the [LICENSE](LICENSE) file for details.

### 🤔 What's Apache 2.0?

The Apache 2.0 license is a **permissive open-source license** that gives you maximum freedom! Here's what makes it special:

**✅ What you CAN do:**
- Use the code commercially 💰
- Modify and distribute it freely 🔄
- Include it in proprietary software 🏢
- Patent protection included 🛡️

**📋 What you MUST do:**
- Include the original copyright notice 📝
- State any changes you made 🔧

**🆚 How it differs from other licenses:**
- **vs MIT**: More explicit about patent rights and contributions
- **vs GPL**: Doesn't require derivative works to be open-source
- **vs BSD**: Includes explicit patent grant and contributor protections
- **vs Proprietary**: Completely free to use and modify

**Perfect for:** Commercial projects, research, and when you want maximum flexibility! 🚀


## 📞 Support

Need help? Got questions? 

- 📖 Check out the [Google Earth Engine documentation](https://developers.google.com/earth-engine)
- 🐛 Open an [issue](https://github.com/bcgov/wps-tutorials/issues)