import bindings as gl
from project import Project

# Current priorities, in order:

def main():
    scale = 1
    size_x = round(720 * scale)
    size_y = round(480 * scale)

    screen = gl.Screen(4, 6, size_x, size_y, "example")

    project = Project("base")
    # project.load("Examples\\Mandelbrot set\\mandel.yaml")
    project.load("debug.yaml")

    frame_rate = project.setup["frame_rate"]
    elapsed_frames = 0

    step_mode = "play"
    scrubbing_repeat_time = 0.1
    key_press_timers = [0, 0]

    if not screen.screen_is_valid():
        raise RuntimeError("Screen was not initialised properly")

    lastX = 0
    lastY = 0
    delta_time = 0
    last_time = 0
    time_since_last_frame = 0
    mouseBound = False
    do_edit = False
    lastMouse = gl.Screen.PressModes.release

    lastspace = False
    lastleft = False
    lastright = False
    laste = False

    force_draw = True

    while not screen.should_close():
        # Process time
        current_time = screen.get_time()
        delta_time = current_time - last_time
        last_time = current_time
        time_since_last_frame += delta_time

        screen.poll()

        # Process mouse movement
        xoffset = screen.pos_x - lastX
        yoffset = lastY - screen.pos_y  # reversed since y - coordinates range from bottom to top
        lastX = screen.pos_x
        lastY = screen.pos_y

        # Legacy mouse binding
        if lastMouse == gl.Screen.PressModes.release:
            if screen.get_mouse_state(gl.Screen.MouseButtons.right) == gl.Screen.PressModes.press:
                mouseBound = not mouseBound

        lastMouse = screen.get_mouse_state(gl.Screen.MouseButtons.right)

        # Assorted key checking
        if screen.get_key_state(gl.Screen.Keys.x) == gl.Screen.PressModes.press:
            screen.set_should_close(True)
        if screen.get_key_state(gl.Screen.Keys.Space) == gl.Screen.PressModes.press:
            if lastspace:
                step_mode = "play" if step_mode == "pause" else "pause"
            lastspace = False
        else:
            lastspace = True

        if screen.get_key_state(gl.Screen.Keys.Left) == gl.Screen.PressModes.press:
            if lastleft:
                elapsed_frames -= 1
                key_press_timers[0] = current_time
            lastleft = False
        else:
            lastleft = True
        if screen.get_key_state(gl.Screen.Keys.Right) == gl.Screen.PressModes.press:
            if lastright:
                elapsed_frames += 1
                key_press_timers[1] = current_time
            lastright = False
        else:
            lastright = True
        if screen.get_key_state(gl.Screen.Keys.e) == gl.Screen.PressModes.press:
            if laste:
                if do_edit:
                    print("Disabling editor")
                    project.disable_edit()
                    do_edit = False
                else:
                    print("Enabling editor")
                    project.enable_edit()
                    do_edit = True
            laste = False
        else:
            laste = True

        screen.set_mouse_capture(mouseBound)

        size_x = screen.screen_x
        size_y = screen.screen_y

        # -------------------------------

        aspect = size_y / size_x

        background_color = project.setup.get("background_color", (0.2, 0.3, 0.3))

        # -------------------------------

        if time_since_last_frame > 1/project.setup.get("frame_rate", 30) or force_draw:
            force_draw = False
            time_since_last_frame = 0
            screen.set_color(*background_color, 1)
            screen.clear(True, True)
            project.render({"debug_draw_bounds": True, "frames": elapsed_frames, "screen_x": size_x,
                            "screen_y": size_y, "aspect": aspect})
            screen.flip()

            if step_mode == "play":
                elapsed_frames += 1

    screen.stop()
    return 0


if __name__ == "__main__":
    main()
