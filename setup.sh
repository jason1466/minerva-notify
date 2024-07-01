wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add
sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list'
apt-get update
apt-get install -y google-chrome-stable
CHROME_VERSION=$(google-chrome --version | grep -oP '\d+\.\d+\.\d+')
mv chromedriver-linux64/chromedriver /usr/local/bin/
sudo chmod +x /usr/local/bin/chromedriver
google-chrome --version
chromedriver --version
echo "export CHROME_BINARY_PATH=/usr/bin/google-chrome" >> ~/.bashrc
echo "export CHROMEDRIVER_PATH=/usr/local/bin/chromedriver" >> ~/.bashrc
source ~/.bashrc
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install webdriver-manager
