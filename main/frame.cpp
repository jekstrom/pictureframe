#include "lib/DEV_Config.h"
#include "lib/EPD.h"
#include "lib/GUI_Paint.h"
#include <stdlib.h>
#include <NetworkClientSecure.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include "time.h"
#include <sys/time.h>
#include "esp_sntp.h"
#include "FS/src/FS.h"
#include "SD.h"
#include "SPI.h"

uint8_t ssid[48] = { 0 };
uint8_t PASSWORD[48] = { 0 };
uint8_t LOCATION[48] = { 0 };
uint8_t MODE[48] = { 0 };
uint8_t IDENTIFIER[48] = { 0 };
const char* ntpServer = "time.nist.gov";
uint64_t next_run_time = 0;

HTTPClient http;

const long  gmtOffset_sec = 0;
const int   daylightOffset_sec = 3600;

int sck = 22;
int miso = 21;
int mosi = 16;
int cs = 27;
using namespace std;

void listDir(fs::FS &fs, const char *dirname, uint8_t levels) {
  Serial.printf("Listing directory: %s\n", dirname);

  File root = fs.open(dirname);
  if (!root) {
    Serial.println("Failed to open directory");
    return;
  }
  if (!root.isDirectory()) {
    Serial.println("Not a directory");
    return;
  }

  File file = root.openNextFile();
  while (file) {
    if (file.isDirectory()) {
      Serial.print("  DIR : ");
      Serial.println(file.name());
      if (levels) {
        listDir(fs, file.path(), levels - 1);
      }
    } else {
      Serial.print("  FILE: ");
      Serial.print(file.name());
      Serial.print("  SIZE: ");
      Serial.println(file.size());
    }
    file = root.openNextFile();
  }
}

void readFile(fs::FS &fs, const char *path) {
  Serial.printf("Reading file: %s\n", path);

  File file = fs.open(path);
  if (!file) {
    Serial.println("Failed to open file for reading");
    return;
  }

  Serial.print("Read from file:\n");
  uint8_t buff[128] = { 0 };
  file.read(buff, sizeof(buff));
  Serial.println((char *) buff);
  uint8_t line[64] = { 0 };
  int y = 0;
  for (int i = 0; i < sizeof(buff); ++i) {
    uint8_t c = buff[i];
    line[y] = c;
    ++y;

    if (((char) c) == '\n') {
      Serial.print("\nline: ");
      Serial.print((char *) line);
      Serial.println();

      uint8_t label[16] = { 0 };
      uint8_t value[48] = { 0 };
      int z = 0;
      int w = 0;
      bool valueStart = false;
      
      // Each line
      for (int x = 0; x < sizeof(line); ++x) {
        uint8_t c2 = line[x];
        if (((char) c2) == '\n') {
          break;
        }
        if (valueStart) {
          value[w] = c2;
          ++w;
        }
        if (((char) c2) != '=' && !valueStart) {
          label[z] = c2;
        } else {
          valueStart = true;
        }
        ++z;
      }
      Serial.print("label: ");
      Serial.print((char *) label);
      Serial.print(" value: ");
      Serial.print((char *) value);
      Serial.println();

      if (strcmp((char *) label, "SSID") == 0) {
        memcpy(ssid, value, sizeof(value));
      }
      if (strcmp((char *) label, (char *)"PASS") == 0) {
        memcpy(PASSWORD, value, sizeof(value));
      }
      if (strcmp((char *) label, (char *)"LOC") == 0) {
        memcpy(LOCATION, value, sizeof(LOCATION));
      }
      if (strcmp((char *) label, (char *)"METRIC") == 0) {}
      if (strcmp((char *) label, (char *)"MODE") == 0) {
        memcpy(MODE, value, sizeof(MODE));
      }
      if (strcmp((char *) label, (char *)"IDENTIFIER") == 0) {
        memcpy(IDENTIFIER, value, sizeof(IDENTIFIER));
      }

      memset(line, 0, sizeof line);
      y = 0;
    }
    if (strcmp((char *) line, (char *)"\n") == 0) {
      break;
    }
  }
}

void printLocalTime(){
  struct tm timeinfo;
  if(!getLocalTime(&timeinfo)){
    Serial.println("Failed to obtain time");
    return;
  }
  Serial.println(&timeinfo, "%A, %B %d %Y %H:%M:%S");
  Serial.print("Day of week: ");
  Serial.println(&timeinfo, "%A");
  Serial.print("Month: ");
  Serial.println(&timeinfo, "%B");
  Serial.print("Day of Month: ");
  Serial.println(&timeinfo, "%d");
  Serial.print("Year: ");
  Serial.println(&timeinfo, "%Y");
  Serial.print("Hour: ");
  Serial.println(&timeinfo, "%H");
  Serial.print("Hour (12 hour format): ");
  Serial.println(&timeinfo, "%I");
  Serial.print("Minute: ");
  Serial.println(&timeinfo, "%M");
  Serial.print("Second: ");
  Serial.println(&timeinfo, "%S");

  Serial.println("Time variables");
  char timeHour[3];
  strftime(timeHour,3, "%H", &timeinfo);
  Serial.println(timeHour);
  char timeWeekDay[10];
  strftime(timeWeekDay,10, "%A", &timeinfo);
  Serial.println(timeWeekDay);
  Serial.println();
}

void setup()
{
    Serial.begin(115200);
    Serial.println("\nsetup");
    int voltage = 0;

    voltage = analogRead(34);
    Serial.println(voltage);
    delay(500);
    voltage = analogRead(34);
    Serial.println(voltage);
    delay(500);
    voltage = analogRead(34);
    Serial.println(voltage);

    if (voltage < 4000) {
      esp_deep_sleep_start();
      return;
    }
    SPI.begin(sck, miso, mosi, cs);
    if (SD.begin(cs)) {
      Serial.println("SD Card Mounted");
    
      uint8_t cardType = SD.cardType();
    
      if (cardType != CARD_NONE) {
        Serial.println("SD card attached");
    
        Serial.print("SD Card Type: ");
        if (cardType == CARD_MMC) {
          Serial.println("MMC");
        } else if (cardType == CARD_SD) {
          Serial.println("SDSC");
        } else if (cardType == CARD_SDHC) {
          Serial.println("SDHC");
        } else {
          Serial.println("UNKNOWN");
        }
      
        uint64_t cardSize = SD.cardSize() / (1024 * 1024);
        Serial.printf("SD Card Size: %lluMB\n", cardSize);
      
        listDir(SD, "/", 0);
        readFile(SD, "/config.txt");
        Serial.printf("Total space: %lluMB\n", SD.totalBytes() / (1024 * 1024));
        Serial.printf("Used space: %lluMB\n", SD.usedBytes() / (1024 * 1024));
      }
    } else {
      Serial.println("SD Card Not Mounted");
    }
      
    WiFi.mode(WIFI_STA); //Optional
    Serial.println("\nConnecting to ");
    Serial.println((char *) ssid);
    WiFi.begin((char *) ssid, (char *) PASSWORD);


    while(WiFi.status() != WL_CONNECTED){
        Serial.print(".");
        delay(100);
    }

    Serial.println("\nConnected to the WiFi network");
    Serial.print("Local ESP32 IP: ");
    Serial.println(WiFi.localIP());
    delay(1000);

    configTime(gmtOffset_sec, daylightOffset_sec, ntpServer);
    sntp_sync_status_t syncStatus = sntp_get_sync_status();
    while (syncStatus != SNTP_SYNC_STATUS_COMPLETED) {
        syncStatus = sntp_get_sync_status();
        delay(100); // Adjust the delay time as per your requirements
    }
    esp_sntp_stop();  //resets syncStatus to SNTP_SYNC_STATUS_RESET for the next time I initiate 
   
    
    struct tm timeinfo;
    if(!getLocalTime(&timeinfo)){
      Serial.println("Failed to obtain time");
      return;
    }
    
    printLocalTime();
    
    char timeHour[3];
    char timeYear[5];
    char timeDay[3];
    char timeMonth[3];
    strftime(timeHour,3, "%H", &timeinfo);
    strftime(timeDay,3, "%d", &timeinfo);
    strftime(timeYear,5, "%Y", &timeinfo);
    strftime(timeMonth,3, "%m", &timeinfo);

    time_t now = mktime(&timeinfo);
    timeval epoch = {now, 0};
    settimeofday((const timeval*)&epoch, 0);
  
    printf("EPD_5in65F_test Demo\r\n");
    DEV_Module_Init();

    printf("e-Paper Init and Clear...\r\n");
    EPD_5IN65F_Init();
   
    printf("init done\r\n");
    EPD_5IN65F_Clear(EPD_5IN65F_WHITE);
    printf("clear done\r\n");
    DEV_Delay_ms(100);

    Serial.print("Mode: ");
    Serial.println((char*)MODE);
  
    if ((WiFi.status() == WL_CONNECTED)) { //Check the current connection status
        NetworkClientSecure *client = new NetworkClientSecure;
        if(client) {
          if (MODE[1] == 0 || (strcmp((char *) MODE, (char *)"weather") == 0)) {
            {
              HTTPClient http;
              int httpCode = -1;
              int falloff = 1;
              while(httpCode < 0) {
                  char *url = (char*)malloc(128 * sizeof(char));
                  sprintf(url, "https://d2x5d7o277kgj7.cloudfront.net/content/%s_%s-%s-%s.bmp", (char *) LOCATION, timeYear, timeMonth, timeDay);
                  Serial.printf("Connecting to %s.\n", url);
                  Serial.printf("WiFi status: %d (expecting %d)\n", WiFi.status(), WL_CONNECTED);
                  http.begin(url); 
                  
                  httpCode = http.GET();
                  Serial.printf("[HTTP] GET... code: %d\n", httpCode);
                  if (falloff > 60) {
                    falloff = 60;
                  }
                  Serial.printf("Waiting %d seconds...\n", falloff);
                  delay(falloff * 1000);
                  falloff = (1 + falloff) * falloff;
              }
          
              if(httpCode > 0) {
                  Serial.printf("[HTTP] GET... code: %d\n", httpCode);
          
                  if(httpCode == HTTP_CODE_OK) {
                      Serial.printf("[HTTP] OK\n");
          
                      int len = http.getSize();
                      Serial.printf("[HTTP] size...: %d\n", len);
          
                      uint8_t buff[EPD_5IN65F_WIDTH/2] = { 0 };
          
                      WiFiClient * stream = http.getStreamPtr();

                      EPD_Setup_Display();
                      while(http.connected() && (len > 0 || len == -1)) {
                          // get available data size
                          size_t size = stream->available();

                          if(size) {
                              int c = stream->readBytes(buff, ((size > sizeof(buff)) ? sizeof(buff) : size));

                              for(int x = 0; x < c; x += 1) {
                                  EPD_5IN65F_SendData2(buff[x]);
                              }
                          
                              if(len > 0) {
                                  len -= c;
                              }
                          }
                          delay(1);
                      }
                      Serial.print("Done display.\n");
                      EPD_Done_Display();
          
                      Serial.println();
                      Serial.print("[HTTP] connection closed or file end.\n");
          
                  }
              } else {
                  Serial.printf("[HTTP] GET... failed, error: %s\n", http.errorToString(httpCode).c_str());
              }
      
              http.end(); //Free the resources
            }
            {
              HTTPClient http;
              int httpCode = -1;
              int falloff = 1;
              while(httpCode < 0) {
                  char *url = (char*)malloc(128 * sizeof(char));
                  sprintf(url, "https://d2x5d7o277kgj7.cloudfront.net/content/%s_%s-%s-%s.txt", (char *) LOCATION, timeYear, timeMonth, timeDay);
                  Serial.printf("Connecting to %s.\n", url);
                  Serial.printf("WiFi status: %d (expecting %d)\n", WiFi.status(), WL_CONNECTED);
                  http.begin(url); 
                  
                  httpCode = http.GET();
                  Serial.printf("[HTTP] GET... code: %d\n", httpCode);
                  if (falloff > 60) {
                    falloff = 60;
                  }
                  Serial.printf("Waiting %d seconds...\n", falloff);
                  delay(falloff * 1000);
                  falloff = (1 + falloff) * falloff;
              }
          
              if(httpCode > 0) {
                  Serial.printf("[HTTP] GET... code: %d\n", httpCode);
          
                  if(httpCode == HTTP_CODE_OK) {
                      Serial.printf("[HTTP] OK\n");
          
                      int len = http.getSize();
                      Serial.printf("[HTTP] size...: %d\n", len);
          
                      uint8_t buff[16] = { 0 };
          
                      WiFiClient * stream = http.getStreamPtr();

                      while(http.connected() && (len > 0 || len == -1)) {
                          // get available data size
                          size_t size = stream->available();

                          if(size) {
                              int c = stream->readBytes(buff, ((size > sizeof(buff)) ? sizeof(buff) : size));                           
                              if(len > 0) {
                                  len -= c;
                              }
                          }
                          delay(1);
                      }            
                      Serial.println();
                      Serial.print("[HTTP] connection closed or file end.\n");
                      
                      sscanf((char *) buff, "%" SCNu64, &next_run_time);
                  }
              } else {
                  Serial.printf("[HTTP] GET... failed, error: %s\n", http.errorToString(httpCode).c_str());
              }
      
              http.end(); //Free the resources
            }
            delete client;
          }
          else if (MODE[1] == 0 || (strcmp((char *) MODE, (char *)"pics") == 0)) {
            {
              HTTPClient http;
              int httpCode = -1;
              int falloff = 1;
              while(httpCode < 0) {
                  char *url = (char*)malloc(128 * sizeof(char));
                  sprintf(url, "https://d2x5d7o277kgj7.cloudfront.net/content/pics/%s_%s-%s-%s.bmp", (char *) IDENTIFIER, timeYear, timeMonth, timeDay);
                  Serial.printf("Connecting to %s.\n", url);
                  Serial.printf("WiFi status: %d (expecting %d)\n", WiFi.status(), WL_CONNECTED);
                  http.begin(url); 
                  
                  httpCode = http.GET();
                  Serial.printf("[HTTP] GET... code: %d\n", httpCode);
                  if (falloff > 60) {
                    falloff = 60;
                  }
                  Serial.printf("Waiting %d seconds...\n", falloff);
                  delay(falloff * 1000);
                  falloff = (1 + falloff) * falloff;
              }
          
              if(httpCode > 0) {
                  Serial.printf("[HTTP] GET... code: %d\n", httpCode);
          
                  if(httpCode == HTTP_CODE_OK) {
                      Serial.printf("[HTTP] OK\n");
          
                      int len = http.getSize();
                      Serial.printf("[HTTP] size...: %d\n", len);
          
                      uint8_t buff[EPD_5IN65F_WIDTH/2] = { 0 };
          
                      WiFiClient * stream = http.getStreamPtr();

                      EPD_Setup_Display();
                      while(http.connected() && (len > 0 || len == -1)) {
                          // get available data size
                          size_t size = stream->available();

                          if(size) {
                              int c = stream->readBytes(buff, ((size > sizeof(buff)) ? sizeof(buff) : size));

                              for(int x = 0; x < c; x += 1) {
                                  EPD_5IN65F_SendData2(buff[x]);
                              }
                          
                              if(len > 0) {
                                  len -= c;
                              }
                          }
                          delay(1);
                      }
                      Serial.print("Done display.\n");
                      EPD_Done_Display();
          
                      Serial.println();
                      Serial.print("[HTTP] connection closed or file end.\n");
          
                  }
              } else {
                  Serial.printf("[HTTP] GET... failed, error: %s\n", http.errorToString(httpCode).c_str());
              }
      
              http.end(); //Free the resources
            }
            delete client;
          }
        }
    }

  printf("Sleep...\r\n");
  EPD_5IN65F_Sleep();
  WiFi.disconnect();
  printf("\n\nGoing to sleep!\n\n");
  if (next_run_time > 0) {
    // Calculate the time until wakeup
    time_t start = mktime(&timeinfo);
    printf("%jd start\n", (intmax_t)start);
    time_t end = next_run_time;
    printf("%jd end\n", (intmax_t)end);

    if (start < end) {
        uint64_t diff;
        diff = (difftime(end, start) + 840) * 1000000;
        printf("Sleep duration: %" PRIu64 " microseconds\n", diff);
        esp_sleep_enable_timer_wakeup(diff);
    } else {
        // If for some reason the next run time is in the past, we want to just default to a 4 hour sleep
        esp_sleep_enable_timer_wakeup(86400000000 / 6); // 4 hours
    }
  } else {
    esp_sleep_enable_timer_wakeup(86400000000); // 1 day
  }
  
  esp_deep_sleep_start();
}

void loop(){}