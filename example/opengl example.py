import math

import bindings as gl


def main():
    size_x = 720
    size_y = 480

    screen = gl.Screen(4, 6, size_x, size_y, "test")

    if not screen.screen_is_valid():
        raise RuntimeError("WadSDSD")

    gl.gl_enable(gl.GL_const.depth_test)

    vao = gl.Vao()

    vertices = [-0.5, -0.5, -0.5, 0.0, 0.0, 0.0, 0.0, 0.0,
                0.5, -0.5, -0.5, 0.0, 0.0, 0.0, 1.0, 0.0,
                0.5, 0.5, -0.5, 0.0, 0.0, 0.0, 1.0, 1.0,
                0.5, 0.5, -0.5, 0.0, 0.0, 0.0, 1.0, 1.0,
                -0.5, 0.5, -0.5, 0.0, 0.0, 0.0, 0.0, 1.0,
                -0.5, -0.5, -0.5, 0.0, 0.0, 0.0, 0.0, 0.0,
                -0.5, -0.5, 0.5, 0.0, 0.0, 0.0, 0.0, 0.0,
                0.5, -0.5, 0.5, 0.0, 0.0, 0.0, 1.0, 0.0,
                0.5, 0.5, 0.5, 0.0, 0.0, 0.0, 1.0, 1.0,
                0.5, 0.5, 0.5, 0.0, 0.0, 0.0, 1.0, 1.0,
                -0.5, 0.5, 0.5, 0.0, 0.0, 0.0, 0.0, 1.0,
                -0.5, -0.5, 0.5, 0.0, 0.0, 0.0, 0.0, 0.0,
                -0.5, 0.5, 0.5, 0.0, 0.0, 0.0, 1.0, 0.0,
                -0.5, 0.5, -0.5, 0.0, 0.0, 0.0, 1.0, 1.0,
                -0.5, -0.5, -0.5, 0.0, 0.0, 0.0, 0.0, 1.0,
                -0.5, -0.5, -0.5, 0.0, 0.0, 0.0, 0.0, 1.0,
                -0.5, -0.5, 0.5, 0.0, 0.0, 0.0, 0.0, 0.0,
                -0.5, 0.5, 0.5, 0.0, 0.0, 0.0, 1.0, 0.0,
                0.5, 0.5, 0.5, 0.0, 0.0, 0.0, 1.0, 0.0,
                0.5, 0.5, -0.5, 0.0, 0.0, 0.0, 1.0, 1.0,
                0.5, -0.5, -0.5, 0.0, 0.0, 0.0, 0.0, 1.0,
                0.5, -0.5, -0.5, 0.0, 0.0, 0.0, 0.0, 1.0,
                0.5, -0.5, 0.5, 0.0, 0.0, 0.0, 0.0, 0.0,
                0.5, 0.5, 0.5, 0.0, 0.0, 0.0, 1.0, 0.0,
                -0.5, -0.5, -0.5, 0.0, 0.0, 0.0, 0.0, 1.0,
                0.5, -0.5, -0.5, 0.0, 0.0, 0.0, 1.0, 1.0,
                0.5, -0.5, 0.5, 0.0, 0.0, 0.0, 1.0, 0.0,
                0.5, -0.5, 0.5, 0.0, 0.0, 0.0, 1.0, 0.0,
                -0.5, -0.5, 0.5, 0.0, 0.0, 0.0, 0.0, 0.0,
                -0.5, -0.5, -0.5, 0.0, 0.0, 0.0, 0.0, 1.0,
                -0.5, 0.5, -0.5, 0.0, 0.0, 0.0, 0.0, 1.0,
                0.5, 0.5, -0.5, 0.0, 0.0, 0.0, 1.0, 1.0,
                0.5, 0.5, 0.5, 0.0, 0.0, 0.0, 1.0, 0.0,
                0.5, 0.5, 0.5, 0.0, 0.0, 0.0, 1.0, 0.0,
                -0.5, 0.5, 0.5, 0.0, 0.0, 0.0, 0.0, 0.0,
                -0.5, 0.5, -0.5, 0.0, 0.0, 0.0, 0.0, 1.0]

    indices = [
        0, 2, 1,
        2, 2, 3,
        3, 7, 5
    ]

    ebo = gl.Ebo()
    ebo.add_data(indices)

    vbo = gl.Vbo()
    vbo.add_data(vertices)

    vao.add_vbo(vbo)
    vao.add_ebo(ebo)

    vao.enable()
    vao.set_row_size(8)
    vao.assign_data(0, 3)
    vao.assign_data(1, 3)
    vao.assign_data(2, 2)

    tex1 = gl.Texture("container.jpg", gl.Texture.Color_modes.rgb)

    tex2 = gl.Texture("awesomeface.png", gl.Texture.Color_modes.rgba)

    debugShader = gl.Shader("vert_basic.vert", "frag_basic.frag")

    debugShader.use()
    debugShader.setInt("texture1", 0)
    debugShader.setInt("texture2", 1)

    cubePositions = [
        0.0, 0.0, 0.0,
        2.0, 5.0, -15.0,
        -1.5, -2.2, -2.5,
        -3.8, -2.0, -12.3,
        2.4, -0.4, -3.5,
        -1.7, 3.0, -7.5,
        1.3, -2.0, -2.5,
        1.5, 2.0, -2.5,
        1.5, 0.2, -1.5,
        -1.3, 1.0, -1.5
    ]
    lastX = 0
    lastY = 0
    deltaTime = 0.0
    lastFrame = 0.0
    mouseBound = True
    lastMouse = gl.Screen.PressModes.release
    camera = gl.Camera()

    while not screen.should_close():
        currentFrame = screen.get_time()
        deltaTime = currentFrame - lastFrame
        lastFrame = currentFrame

        screen.poll()

        xoffset = screen.pos_x - lastX
        yoffset = lastY - screen.pos_y  # reversed since y - coordinates range from bottom to top
        lastX = screen.pos_x
        lastY = screen.pos_y

        camera.process_mouse(xoffset, yoffset)

        if lastMouse == gl.Screen.PressModes.release:
            if screen.get_mouse_state(gl.Screen.MouseButtons.right) == gl.Screen.PressModes.press:
                mouseBound = not mouseBound

        lastMouse = screen.get_mouse_state(gl.Screen.MouseButtons.right)

        if screen.get_key_state(gl.Screen.Keys.x) == gl.Screen.PressModes.press:
            screen.set_should_close(True)
        if screen.get_key_state(gl.Screen.Keys.w) == gl.Screen.PressModes.press:
            camera.process_keyboard(gl.Camera.Camera_Movement.forward, deltaTime)
        if screen.get_key_state(gl.Screen.Keys.s) == gl.Screen.PressModes.press:
            camera.process_keyboard(gl.Camera.Camera_Movement.back, deltaTime)
        if screen.get_key_state(gl.Screen.Keys.a) == gl.Screen.PressModes.press:
            camera.process_keyboard(gl.Camera.Camera_Movement.left, deltaTime)
        if screen.get_key_state(gl.Screen.Keys.d) == gl.Screen.PressModes.press:
            camera.process_keyboard(gl.Camera.Camera_Movement.right, deltaTime)

        screen.set_mouse_capture(mouseBound)
        camera.process_scroll(screen.scroll_y)

        # -------------------------------
        screen.set_color(0.2, 0.3, 0.3, 1)
        screen.clear(True, True)

        model = gl.Mat4(1.0)

        model = gl.rotate(model, screen.get_time() * gl.radians(50.0), gl.Vec3(0.5, 1.0, 0.0))

        view = camera.get_view_matrix()

        direction = gl.Vec3()
        direction.x = math.cos(gl.radians(camera.yaw)) * math.cos(gl.radians(camera.pitch))
        direction.y = math.sin(gl.radians(camera.pitch))
        direction.z = math.sin(gl.radians(camera.yaw)) * math.cos(gl.radians(camera.pitch))

        projection = gl.Mat4()
        projection = gl.perspective(gl.radians(camera.zoom), 800.0 / 600.0, 0.1, 100.0)

        timeValue = screen.get_time()

        greenValue = (math.sin(timeValue) / 2.0) + 0.5

        debugShader.use()
        debugShader.setFloat("green", greenValue)
        debugShader.setFloat("mix", greenValue)

        debugShader.setMat4("model", model)
        debugShader.setMat4("view", view)
        debugShader.setMat4("projection", projection)

        tex1.bind(gl.Texture.Texture_ids.tex_0)
        tex2.bind(gl.Texture.Texture_ids.tex_1)
        vao.draw_mode(gl.Vao.Modes.fill)

        for i in range(10):
            model = gl.Mat4(1.0)
            model = gl.translate(model, gl.Vec3(*cubePositions[3 * i:3 * i + 3]))
            angle = 20.0 * i
            model = gl.rotate(model, gl.radians(angle), gl.Vec3(1.0, 0.3, 0.5))
            model = gl.rotate(model, screen.get_time() * gl.radians(50.0), gl.Vec3(0.5, 1, 0))

            debugShader.setMat4("model", model)

            vao.draw_elements(0, 0, True)

        screen.flip()

    screen.stop()
    return 0

    # gl.main(screen)


main()

'''for l in [cubePositions[i:i + 3] for i in range(0, len(cubePositions), 3)]:
        l = [str(q) for q in l]
        print(", ".join(l) + ",") '''
