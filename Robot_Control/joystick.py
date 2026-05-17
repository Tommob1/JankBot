import hid

VID = 0x046D
PID = 0xC215

def list_hid_devices():
    print("Listing all HID devices:")
    for device in hid.enumerate():
        print(f"VID: {hex(device['vendor_id'])}, PID: {hex(device['product_id'])}, Product: {device['product_string']}")

def read_joystick_data():
    print(f"\nConnecting to device: VID={hex(VID)}, PID={hex(PID)}")
    try:
        joystick = hid.device()
        joystick.open(VID, PID)
        print(f"Connected to {joystick.get_product_string()}")

        print("Listening for joystick input... Move the stick or press buttons. (Ctrl+C to exit)\n")
        while True:
            data = joystick.read(64)
            if data:
                print(f"Raw Data: {data}")
    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        joystick.close()
        print("Joystick connection closed.")

if __name__ == "__main__":
    list_hid_devices()
    read_joystick_data()
