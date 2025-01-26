from vector import Vector
import pygame
import math


class Image:
    """Detta ska grundlägga informationsstrukturen för vår bild och innehålla relaterade operationer."""
    def __init__(self, width, height):
        self.width = width
        self.height = height
        # En (height x width)-nested list - som representerar varje pixel i användargränssnittet i form av vektorn (R,G,B).
        self.pixels = [[Vector(0, 0, 0) for _ in range(width)] for _ in range(height)]

    def intryck(self, x, y, fordelning):
        """Fördelar RGB värden till alla pixlar tomma pixlar på användargränssnittet."""
        self.pixels[y][x] = fordelning


class Sjelvarenderingen:
    """Här sker själva renderingen."""
    def __init__(self,reflektions_djup=20, delta=0.0001):
        self.reflektions_djup = reflektions_djup
        self.delta = delta

    def render(self, scene):
        """Utför själva renderingen av 3D-strukturerna utifrån information om scenen.
        Alltså alla variabler vi kan få tillgång till via scene-variabeln."""
        width = scene.width
        height = scene.height
        ratio = width / height
        x0 = -1.0
        x1 = +1.0
        xstep = (x1 - x0) / (width - 1)
        y0 = -1.0 / ratio
        y1 = +1.0 / ratio
        ystep = (y1 - y0) / (height - 1)

        camera = scene.camera

        # Vår (width x height)-lista med vektorer för varje pixels RGB-färg.
        pixels = Image(width, height)

        for j in range(height):
            y = y0 + j * ystep
            for i in range(width):
                x = x0 + i * xstep
                # Stråle från en pixel i kameravinkeln till klotet
                ray = Ray(camera, Point(x, y) - camera)
                # Applicerar resultatet av raytracing-funktionen (som inverkar på alla pixlar) till varje pixel.
                pixels.intryck(i, j, self.ray_trace(ray, scene))

        # Returnerar information med en ny (m x n) lista om bilden.
        return pixels

    def ray_trace(self, ray, scene, depth=0):
        """Utför ray-tracingfunktionen med strålen som den tar in och med hjälp av informationen
        om scenen. Desstuom fördefinierar vi djupet på antalet speglingar som 0 (depth = 0)."""
        # Svart färg
        color = Vector(0, 0, 0)

        dist_hit, obj_hit = self.find_nearest(ray, scene)
        if obj_hit is None:
            # Ifall vi inte finner ett objekt returnerar vi bakgrundsfärgen svart.
            return color

        # De punkterna på bilden som användarsnittet ser.
        hit_pos = ray.u + ray.v * dist_hit
        # Positionen på objekten som är rätvinkliga mot solens stråle.
        hit_normal = obj_hit.normal(hit_pos)
        color += self.color_at(obj_hit, hit_pos, scene, hit_normal)

        # Reflektion: Rekursiv raytracing
        if depth < self.reflektions_djup:
            new_ray_pos = hit_pos + hit_normal * self.delta
            new_ray_rikt = ray.v - 2 * ray.v.dot_product(hit_normal)*hit_normal
            ref_ray = Ray(new_ray_pos, new_ray_rikt)

            # Effekt ur attenuation: Förlust av ljusenergi efter varje reflektion.
            color += self.ray_trace(ref_ray, scene, depth + 1) * obj_hit.material.reflection_coef

        return color

    def color_at(self, obj_hit, hit_pos, scene, normal):
        """Här bestämmer vi vilken färg pixlarna får."""

        # Egenskaperna om materialet av objektet som träffas.
        material = obj_hit.material

        # Konstanter för objektet
        obj_color = material.color
        from_cam_to_hit = scene.camera - hit_pos
        # Andelen av helvit ljus = ambiens * vit ljus
        color = material.ambient * Vector(255, 255, 255)
        spekular_k = 50

        for light in scene.lights:

            to_light = Ray(hit_pos, light.position - hit_pos)
            # Applicerar objekt-specifik skugga enligt Lamberts skuggningsmodell.
            color += obj_color * material.diffues * (max(normal.dot_product(to_light.v), 0))
            # Applicerar spekular-skuggning enligt Blinn-Phongmodellen.
            half_vector = (to_light.v + from_cam_to_hit).normalize()
            color += light.color * material.specular * max(normal.dot_product(half_vector), 0) ** spekular_k
            mini, objetiv = self.find_nearest(to_light, scene)
            # En lista med längder från ljuskällan till objektet.
            for obj in range(len(scene.objects)):
                if scene.objects[obj].intersektion(to_light) is not None:
                    if float(scene.objects[obj].intersektion(to_light)) >= float(mini):
                        color -= light.color * material.specular * max(normal.dot_product(half_vector), 0) ** spekular_k
                        color -= obj_color * material.diffues * (max(normal.dot_product(to_light.v), 0))

        # Vi klampar funktionen så att skugg-avdragningen inte kommer under 0.
        color = Vector(clamp(color.x, 0, 255), clamp(color.y, 0, 255), clamp(color.z, 0, 255))

        return color

    def find_nearest(self, ray, scene):
        """Hittar objektet som är närmast en linje,
        samt misnta avståndet från dess linjes startpunkt."""
        minsta_langd = None
        object_hit = None

        # Vi checkar ser för varje obejtk ifall strålen som kommer från pixeln (x, y) i användarsnittet träffar objekt.
        # Ifall den gör det hittar vi minsta längden.
        for obj in scene.objects:
            langd = obj.intersektion(ray)
            if langd is not None and (object_hit is None or langd < minsta_langd):
                minsta_langd = langd
                # För att returnera objektet som träffades. Exempelvis Sphere()....
                object_hit = obj

        return (minsta_langd, object_hit)


class Point(Vector):
    """Vi skriver bara detta för att kunna använda samma operationer som vi gör
     på vektorer, fast på punkter som vi noterar Point."""
    pass


class Ray:
    """Vi behöver denna klass för alla våra linjeekvationer
    med initsialiserad normalisering för riktningsvektorn."""

    def __init__(self, u, v):
        """Tar startpunkt u och riktningsvektor v (som normaliseras)."""
        self.u = u
        self.v = v.normalize()


class Sphere:
    """Information om sfärobjektet, samt operationer relaterade till objektet."""

    def __init__(self, center, radius, material):
        self.center = center
        self.radius = radius
        self.material = material

    def intersektion(self, ray):
        """Räknar ut avståndet från en linjeekvations definierade startpunkt (ray.u)
        till en korsning med sfären och returnerar None ifall linjen inte träffar."""
        sphere_to_ray = ray.u - self.center
        b = 2 * ray.v.dot_product(sphere_to_ray)
        c = sphere_to_ray.dot_product(sphere_to_ray) - self.radius * self.radius
        discriminant = b * b - 4 * c

        if discriminant >= 0:

            distupp = (-b - math.sqrt(discriminant)) / 2

            if distupp > 0:
                return distupp

        else:  # Returnerar None ifall discriminant < 0. Alltså objektet träffas inte.
            return None

    def normal(self, surface_point):
        """Räknar ut normalen från en punkt på ytan."""
        return (surface_point - self.center).normalize()


class Scene:
    """Scene har all information om själva scenen användargränssnittet ser
    och används för att komma åt följande variabler."""

    def __init__(self, camera, objects, lights, width, height):
        self.camera = camera
        self.objects = objects
        self.lights = lights
        self.width = width
        self.height = height


class Light:
    """En klass för att strukturerat handhålla information om ljuskällan."""
    def __init__(self, position, color=Vector(255, 255, 255)):
        self.position = position
        self.color = color


class Material:
    """En klass för att handhålla information om materialet i
    relation till det teoretiskt skapade rummet. Här tas rummets ambiens
    och objektens ljusreflektion till hänsyn. NOTERA: Inte bildreflektion!."""
    def __init__(self, color, ambient=0.05, diffues=0.8, specular=0.9, reflection_coef = 0.5):
        self.color = color
        self.ambient = ambient
        self.diffues = diffues
        self.specular = specular
        self.reflection_coef = reflection_coef


class Clickcirkel:
    """En klass för att handhålla operationer om vad som händer när man trycker på sfären."""
    def __init__(self, scene, centrum, radius):
        self.scene = scene
        self.centrum = centrum
        self.raidus = radius

    def var_click_po_cirkel(self, tryck_x, tryck_y, scene):
        """Returnerar var 3D-koordinaterna man track på i skärmen träffade en sfär
         och returnerar None ifall den inte träffar sfären."""
        ratio = scene.width / scene.height
        x0 = -1
        x1 = 1.0
        y0 = -1 / ratio
        y1 = 1.0 / ratio
        x_step = (x1 - x0) / (self.scene.width - 1)
        y_step = (y1 - y0) / (self.scene.height - 1)

        x = x0 + tryck_x * x_step
        y = y0 + tryck_y * y_step

        # Ray är (x, y, z) där z kan vara vilket tal somhälst och x och y är konstanta
        # (de pixlarna vi valde på skärmen). Alltså har vi riktningsvektorn (x,y,0)
        klot = self.scene.objects[0]
        kamera_till_klot = Ray(Vector(x, y, -1), Vector(0, 0, 1))
        if klot.intersektion(kamera_till_klot) is not None:
            punkt = kamera_till_klot.u + kamera_till_klot.v * klot.intersektion(kamera_till_klot)
            return punkt
        else:
            return None

    def sol_forflyttning(self, lx, ly, lz, tryckt_x_koordinat, tryck_y_koordinat):
        """Flyttar ljuskällan till den nya koordinaten som projecerats utav den valda pixeln på sfären yta."""
        ray = Ray(self.centrum, self.var_click_po_cirkel(tryckt_x_koordinat, tryck_y_koordinat, self.scene))
        dist = math.sqrt(lx ** 2 + ly ** 2 + lz ** 2)
        faktor = dist / ray.v.magnitude()
        lx_ny, ly_ny, lz_ny = faktor * ray.v.x, faktor * ray.v.y, faktor * ray.v.z
        return lx_ny, ly_ny, lz_ny

def clamp(n, mini, maxi):
    """En instängningsfunktion som håller värden innanför ett intervall [mini,maxi]."""
    return max(min(maxi, n), mini)


def main():
    width = 900
    height = 700
    camera = Vector(0, 0, -1)

    # Position och storlek av cirkel.
    cirkelns_centrum = Point(0, 0, 0)
    r = 0.2

    pygame.init()
    pygame.display.set_caption("Raytracing engine")
    screen = pygame.display.set_mode((width, height))
    screen.fill((0, 0, 0))
    pygame.display.flip()

    lx = 5
    ly = -3
    lz = -5

    lights = [Light(Point(lx, ly, lz), Vector(255, 255, 255))]
    # Fyll på listan nedanför med fler objekt ifall du vill.
    objects = [Sphere(cirkelns_centrum, r, Material(Vector(255,54,89))),
               Sphere(Point(0, 9000.3, 0), 9000, Material(Vector(50, 113, 95))),
               Sphere(Point(0.65, -0.45, -0.05), 0.25, Material(Vector(100, 0, 255))),
                Sphere(Point(0.4, -0.07, -0.22), 0.12, Material(Vector(100, 255, 50)))
               ]

    scene = Scene(camera, objects, lights, width, height)

    # Information om texten.
    font = pygame.font.Font(None, int(width / 70 + height / 60))
    text_tryck_nu = font.render("Click anywhere on the centersphere to project the lightsource. Click 'esc' to close program.", True,(150, 150, 150))
    text_tryck_inte = font.render("Wait for the programme to load ...", True, (150, 150, 150))
    text_loda = text_tryck_nu.get_rect(center=(33 * width // 80, height // 6))

    # Tryckområdet
    tryck_omrade = pygame.Rect(0, 0, width, height)

    def ifyllnad(surface, lx, ly, lz):
        """Fyller i alla pixlarna på skärmen."""
        # Byter ut ljuset som tidigare fanns mot ett nytt ljus på en annan position
        scene.lights = [Light(Point(lx, ly, lz), Vector(255, 255, 255))]

        engine = Sjelvarenderingen()
        image = engine.render(scene)

        for xx in range(scene.width):
            for yy in range(scene.height):
                a = image.pixels[yy][xx]
                konvert = tuple([clamp(a.x, 0, 255), clamp(a.y, 0, 255), clamp(a.z, 0, 255)])
                surface.set_at((xx, yy), konvert)
    def tre_d_system(w, h, font):
        """Genererar 3D-koordinatsystemet i högra nedre hörnet."""
        # positionen av origo i det lilla koordinatsystemet
        pos = (4 * w // 5, 4 * h // 5)

        # Koordinataxlarnas längd
        axl = w // 20 + h // 20

        # Längden av rutsidorna i det inzommade koordinatsystemet som hjälper modulera det.
        kv = (w + h) // 320

        rod = (200, 20, 20)
        gron = (20, 200, 20)
        blo = (20, 20, 200)
        text_x = font.render('+x', True, rod)
        text_y = font.render('-y', True, gron)
        text_z = font.render('-z', True, blo)

        # X-axeln + pil med riktning
        pygame.draw.line(screen, rod, (pos[0] - axl, pos[1]), (pos[0] + axl, pos[1]), 2)
        pygame.draw.polygon(screen, rod,
                            [(pos[0] + axl - 2 * kv, pos[1] - kv),
                             (pos[0] + axl, pos[1]),
                             (pos[0] + axl - 2 * kv, pos[1] + kv)])

        # Y-axeln + pil med riktning
        pygame.draw.line(screen, gron, (pos[0], pos[1] - axl), (pos[0], pos[1] + axl), 2)
        pygame.draw.polygon(screen, gron, [(pos[0] - kv, pos[1] - axl + 2 * kv),
                                           (pos[0], pos[1] - axl),
                                           (pos[0] + 5, pos[1] - axl + 2 * kv)])

        # Z-axeln + pil med riktning
        pygame.draw.line(screen, blo, (pos[0] + axl // 2, pos[1] - axl // 2), (pos[0] - axl // 2, pos[1] + axl // 2),
                         2)
        pygame.draw.polygon(screen, blo, [(pos[0] - axl // 2 + 3 * kv, pos[1] + axl // 2 - kv),
                                          (pos[0] - axl // 2, pos[1] + axl // 2),
                                          (pos[0] - axl // 2, pos[1] + axl // 2 - 2 * kv)])

        screen.blit(text_x, (pos[0] + axl - 2 * kv, pos[1] - 4 * kv))
        screen.blit(text_y, (pos[0] + 2 * kv, pos[1] - axl - kv))
        screen.blit(text_z, (pos[0] - axl // 2 + 2 * kv, pos[1] + axl // 2 - kv))
    def pause_happening(text, text_loda, cirkelns_centrum, r):
        """En operation som ser till att programmet är pausat när man inte interagerar med det,
        och vidare exekveterar programmet när man interagerar med det."""
        pause = True

        while pause:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    """Samma typ av programavslutning som innan."""
                    pygame.quit()
                    quit()

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        """Avslutar programmet."""
                        pygame.quit()
                        quit()

                if event.type == pygame.MOUSEBUTTONDOWN:
                    # Om man utför ett tryck på skärmen:
                    if tryck_omrade.collidepoint(event.pos):
                        tryck_po_cikeln = Clickcirkel(scene, cirkelns_centrum, r)
                        kor = tryck_po_cikeln.var_click_po_cirkel(event.pos[0], event.pos[1], scene)

                        if bool(tryck_po_cikeln.var_click_po_cirkel(event.pos[0], event.pos[1], scene)):
                            lx_ny, ly_ny, lz_ny = tryck_po_cikeln.sol_forflyttning(lx, ly, lz, event.pos[0],
                                                                                   event.pos[1])
                            return lx_ny, ly_ny, lz_ny, kor

            screen.blit(text, text_loda)
            pygame.display.update()

    # Därifrån själva funktionen exekveteras
    running = True
    while running:
        for event in pygame.event.get():

            screen.blit(text_tryck_inte, text_loda)
            pygame.display.update()
            ifyllnad(screen, lx, ly, lz)
            tre_d_system(width, height, font)
            lx, ly, lz, kor = pause_happening(text_tryck_nu, text_loda, cirkelns_centrum, r)

            screen.fill((0, 0, 0))
            text_for_kor = font.render('You clicked on coordinates ' + str(kor) + ' på sfären.', True, (150, 150, 150))
            text_loda_kor = text_for_kor.get_rect(center=(width // 2, height // 4 + width // 30 + height // 30))
            screen.blit(text_for_kor, text_loda_kor)

            if event.type == pygame.QUIT:
                running = False

        pygame.display.update()


if __name__ == "__main__":
    main()

