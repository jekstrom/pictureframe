idf_component_register(SRCS "frame.cpp" "lib/DEV_Config.cpp" "lib/utility/EPD_5in65f.cpp" "lib/utility/epdif.cpp" 
                    INCLUDE_DIRS "." "lib" "lib/utility"
                    PRIV_REQUIRES arduino-esp32 nvs_flash esp_wifi esp_driver_gpio esp_timer driver esp_partition esp_eth mbedtls esp_http_client
                    PRIV_INCLUDE_DIRS "$ENV{LIB_PATH}/arduino-esp32/libraries"
                    "$ENV{LIB_PATH}/arduino-esp32/libraries/Wire/src/"
                    "$ENV{LIB_PATH}/arduino-esp32/libraries/Network/src/"
                    "$ENV{LIB_PATH}/arduino-esp32/libraries/HTTPClient/src"
                    "$ENV{LIB_PATH}/arduino-esp32/libraries/NetworkClientSecure/src"
                    "$ENV{LIB_PATH}/arduino-esp32/libraries/WiFi/src"
                    "$ENV{LIB_PATH}/arduino-esp32/libraries/FS/src"
                    "$ENV{LIB_PATH}/arduino-esp32/libraries/SD/src"
                    "$ENV{LIB_PATH}/arduino-esp32/libraries/SPI/src"
                    "$ENV{LIB_PATH}/arduino-esp32/cores/esp32"
                    "$ENV{LIB_PATH}/arduino-esp32/variants/esp32da")
