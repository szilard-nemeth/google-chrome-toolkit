import datetime
import os

from pythoncommons.file_utils import FileUtils

PORT = "9222"
ABSTRACT_SOCKET_NAME = "chrome_devtools_remote"


def main():
    # checking for connected devices
    adb_out = os.popen("adb devices -l").read()
    second_line = adb_out.split('\n', 1)[1]
    device_info_list = second_line.split("device")[1:]
    if not device_info_list:
        print("No connected device found!")
        exit(1)
    device_info = "".join([d.strip() for d in device_info_list])
    print("Detected connected device: " + device_info)

    # Get forward list
    forward_list = os.popen("adb forward --list").read().strip()
    if not forward_list:
        print("Port forward not detected. Opening one port forwarding TCP socket on port %s" % PORT)
        os.system("adb forward tcp:{} localabstract:{}".format(PORT, ABSTRACT_SOCKET_NAME))
    forward_list = os.popen("adb forward --list").read().strip()
    if not forward_list:
        raise ValueError("Cannot create port forwarding TCP socket on port %s!" % PORT)
    print("Forward list: " + forward_list)

    data = load_json("http://localhost:{}/json/list".format(PORT))

    # Order by ids
    ordered_data = sorted(data, key=lambda d: d['id'])
    # print("Ordered data: " + str(ordered_data))

    urls = [d['url'] for d in ordered_data]
    # print("URLs: " + str(urls))

    final_result = "\n".join(urls)
    filename = os.sep + "tmp" + os.sep + "webpages-phone-" + datetime.datetime.now().strftime('%Y%m%d_%H%M%S.txt')
    FileUtils.write_to_file(filename, final_result)
    print("Pages saved to file: " + filename)
    print("Opening file: " + filename)
    os.system("subl " + filename)


def load_json(url):
    import requests
    r = requests.get(url)
    # print("Received data: " + str(r.text))
    return r.json()


if __name__ == '__main__':
    main()
