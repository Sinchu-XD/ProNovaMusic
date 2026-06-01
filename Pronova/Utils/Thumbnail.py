import random
import os
import re
import uuid
import aiofiles
import aiohttp
from traceback import format_exc
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

import logging

logger = logging.getLogger("Pronova.Thumbnail")


def changeImageSize(maxWidth, maxHeight, image):
    widthRatio = maxWidth / image.size[0]
    heightRatio = maxHeight / image.size[1]
    newWidth = int(widthRatio * image.size[0])
    newHeight = int(heightRatio * image.size[1])
    return image.resize((newWidth, newHeight))


def wrap_text(text, font, max_width, draw):
    if not text:
        return ["Now Playing"]

    lines = []
    words = text.split()
    current_line = ""

    for word in words:
        test_line = current_line + (" " if current_line else "") + word
        try:
            bbox = draw.textbbox((0, 0), test_line, font=font)
            text_width = bbox[2] - bbox[0]
        except Exception:
            text_width = len(test_line) * 10

        if text_width <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = word

    if current_line:
        lines.append(current_line)

    if not lines:
        lines = ["Now Playing"]

    return lines[:2]


def random_color():
    return (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))


def generate_gradient(width, height, start_color, end_color):
    base = Image.new("RGBA", (width, height), start_color)
    top = Image.new("RGBA", (width, height), end_color)
    mask = Image.new("L", (width, height))
    mask_data = []
    for y in range(height):
        mask_data.extend([int(60 * (y / height))] * width)
    mask.putdata(mask_data)
    base.paste(top, (0, 0), mask)
    return base


def add_border(image, border_width, border_color):
    width, height = image.size
    new_width = width + 2 * border_width
    new_height = height + 2 * border_width
    new_image = Image.new("RGBA", (new_width, new_height), border_color)
    new_image.paste(image, (border_width, border_width))
    return new_image


def crop_center_circle(img, output_size, border, border_color, crop_scale=1.5):
    half_the_width = img.size[0] / 2
    half_the_height = img.size[1] / 2
    larger_size = int(output_size * crop_scale)
    img = img.crop(
        (
            half_the_width - larger_size / 2,
            half_the_height - larger_size / 2,
            half_the_width + larger_size / 2,
            half_the_height + larger_size / 2,
        )
    )

    img = img.resize((output_size - 2 * border, output_size - 2 * border))

    final_img = Image.new("RGBA", (output_size, output_size), border_color)

    mask_main = Image.new("L", (output_size - 2 * border, output_size - 2 * border), 0)
    draw_main = ImageDraw.Draw(mask_main)
    draw_main.ellipse(
        (0, 0, output_size - 2 * border, output_size - 2 * border), fill=255
    )

    final_img.paste(img, (border, border), mask_main)

    mask_border = Image.new("L", (output_size, output_size), 0)
    draw_border = ImageDraw.Draw(mask_border)
    draw_border.ellipse((0, 0, output_size, output_size), fill=255)

    result = Image.composite(
        final_img, Image.new("RGBA", final_img.size, (0, 0, 0, 0)), mask_border
    )

    return result


def draw_text_with_shadow(
    background, draw, position, text, font, fill, shadow_offset=(3, 3), shadow_blur=5
):
    shadow = Image.new("RGBA", background.size, (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)
    shadow_draw.text(position, text, font=font, fill="black")
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=shadow_blur))
    background.paste(shadow, shadow_offset, shadow)
    draw.text(position, text, font=font, fill=fill)


def _load_font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()


async def get_thumb(title, duration, thumbnail, channel=None, views=None, videoid=None):
    try:
        random_id = str(uuid.uuid4())[:8]
        temp_files_to_delete = []

        if videoid:
            videoid = re.sub(r'[/\\:*?"<>|]', "_", str(videoid))
        else:
            videoid = "unknown"

        if thumbnail is None:
            thumbnail = "thumbnail.png"

        os.makedirs("cache", exist_ok=True)

        if os.path.exists(thumbnail):
            image_path = thumbnail
            if not title:
                title = "Now Playing"
        else:
            temp_thumb_path = f"cache/thumb_{random_id}_{videoid}.png"
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        thumbnail, timeout=aiohttp.ClientTimeout(total=15)
                    ) as resp:
                        if resp.status == 200:
                            async with aiofiles.open(temp_thumb_path, mode="wb") as f:
                                await f.write(await resp.read())
                            image_path = temp_thumb_path
                            temp_files_to_delete.append(temp_thumb_path)
                        else:
                            image_path = "thumbnail.png"
            except Exception:
                logger.warning(f"Thumb download failed for {videoid}, using fallback")
                image_path = "thumbnail.png"

        if not os.path.exists(image_path):
            logger.error(f"No image found for {videoid}")
            return None

        channel = channel or "Telegram"
        views = str(views) if views else "1M"

        youtube = Image.open(image_path)
        image1 = changeImageSize(1280, 720, youtube)
        image2 = image1.convert("RGBA")

        background = image2.filter(filter=ImageFilter.GaussianBlur(30))
        enhancer = ImageEnhance.Brightness(background)
        background = enhancer.enhance(0.3)

        gradient_colors = [
            (138, 43, 226),
            (220, 20, 60),
            (255, 140, 0),
            (0, 191, 255),
            (255, 20, 147),
            (50, 205, 50),
        ]

        primary_color = random.choice(gradient_colors)
        gradient_colors_copy = [c for c in gradient_colors if c != primary_color]
        secondary_color = random.choice(gradient_colors_copy)

        gradient = Image.new("RGBA", (1280, 720), primary_color + (0,))
        for y in range(720):
            alpha = int(180 * (y / 720))
            r = int(primary_color[0] + (secondary_color[0] - primary_color[0]) * (y / 720))
            g = int(primary_color[1] + (secondary_color[1] - primary_color[1]) * (y / 720))
            b = int(primary_color[2] + (secondary_color[2] - primary_color[2]) * (y / 720))
            for x in range(1280):
                gradient.putpixel((x, y), (r, g, b, alpha))

        background = Image.alpha_composite(background, gradient)

        draw = ImageDraw.Draw(background)

        title_font = _load_font("NotoSansDevanagari-Bold.ttf", 52) or _load_font("font.ttf", 52)
        subtitle_font = _load_font("font.ttf", 28)
        info_font = _load_font("font2.ttf", 24)
        time_font = _load_font("font.ttf", 26)
        channel_font = _load_font("font.ttf", 36)
        views_font = _load_font("font.ttf", 28)

        card_x, card_y = 80, 80
        card_width, card_height = 1120, 560

        glass_card = Image.new("RGBA", (card_width, card_height), (255, 255, 255, 0))
        glass_draw = ImageDraw.Draw(glass_card)
        glass_draw.rounded_rectangle(
            [(0, 0), (card_width, card_height)],
            radius=30,
            fill=(255, 255, 255, 25),
            outline=(255, 255, 255, 80),
            width=2,
        )
        glass_card = glass_card.filter(ImageFilter.GaussianBlur(2))
        background.paste(glass_card, (card_x, card_y), glass_card)

        album_size = 340
        album_border = 8
        neon_glow_color = primary_color

        for glow_layer in range(3, 0, -1):
            glow_size = album_size + (glow_layer * 20)
            glow = Image.new("RGBA", (glow_size, glow_size), (0, 0, 0, 0))
            glow_draw = ImageDraw.Draw(glow)
            glow_alpha = max(10, 50 - (glow_layer * 15))
            glow_draw.ellipse(
                [(0, 0), (glow_size, glow_size)],
                fill=neon_glow_color + (glow_alpha,),
            )
            glow = glow.filter(ImageFilter.GaussianBlur(15 + glow_layer * 5))
            glow_pos = (
                card_x + 60 - (glow_size - album_size) // 2,
                card_y + (card_height - glow_size) // 2,
            )
            background.paste(glow, glow_pos, glow)

        circle_thumbnail = crop_center_circle(
            youtube, album_size, album_border, (255, 255, 255), crop_scale=1.3
        )
        album_position = (card_x + 60, card_y + (card_height - album_size) // 2)
        background.paste(circle_thumbnail, album_position, circle_thumbnail)

        text_x = card_x + album_size + 120
        text_area_width = card_width - album_size - 180

        title1 = wrap_text(title, title_font, text_area_width, draw)
        title_y = card_y + 100

        label_text = "POWERED BY PRONOVA MUSIC"
        try:
            label_font = _load_font("Cinzel-Black.ttf", 42)
            label_bbox = draw.textbbox((0, 0), label_text, font=label_font)
            label_width = label_bbox[2] - label_bbox[0]
            label_x = (background.width // 2) - (label_width // 2)
            label_y = card_y + 18
            draw_text_with_shadow(
                background, draw, (label_x, label_y), label_text, label_font,
                random_color(), shadow_offset=(3, 3), shadow_blur=5,
            )
        except Exception:
            pass

        for i, line in enumerate(title1):
            draw_text_with_shadow(
                background, draw, (text_x, title_y + (i * 60)), line, title_font,
                (255, 255, 255), shadow_offset=(3, 3), shadow_blur=6,
            )

        artist_y = title_y + 150
        draw_text_with_shadow(
            background, draw, (text_x, artist_y), str(channel), channel_font,
            random_color(), shadow_offset=(2, 2), shadow_blur=4,
        )

        views_text = str(views)[:23]
        draw_text_with_shadow(
            background, draw, (text_x, artist_y + 55), views_text, views_font,
            random_color(), shadow_offset=(2, 2), shadow_blur=3,
        )

        progress_y = card_y + card_height - 140
        progress_x = text_x
        progress_width = text_area_width - 20
        progress_height = 6

        track_bg = Image.new("RGBA", (progress_width, progress_height + 20), (0, 0, 0, 0))
        track_draw = ImageDraw.Draw(track_bg)
        track_draw.rounded_rectangle(
            [(0, 10), (progress_width, 10 + progress_height)],
            radius=progress_height // 2,
            fill=(255, 255, 255, 60),
        )
        background.paste(track_bg, (progress_x, progress_y), track_bg)

        if duration != "Live":
            progress_percentage = random.uniform(0.15, 0.85)
            filled_width = int(progress_width * progress_percentage)

            progress_bar = Image.new("RGBA", (filled_width, progress_height + 20), (0, 0, 0, 0))
            progress_draw = ImageDraw.Draw(progress_bar)

            for x in range(filled_width):
                progress_ratio = x / max(filled_width, 1)
                r_c = int(primary_color[0] + (secondary_color[0] - primary_color[0]) * progress_ratio)
                g_c = int(primary_color[1] + (secondary_color[1] - primary_color[1]) * progress_ratio)
                b_c = int(primary_color[2] + (secondary_color[2] - primary_color[2]) * progress_ratio)
                progress_draw.line(
                    [(x, 10), (x, 10 + progress_height)], fill=(r_c, g_c, b_c, 255), width=1
                )

            progress_bar = progress_bar.filter(ImageFilter.GaussianBlur(1))
            background.paste(progress_bar, (progress_x, progress_y), progress_bar)

            indicator_x = progress_x + filled_width
            indicator_y = progress_y + 13
            indicator_radius = 10

            for glow in range(3, 0, -1):
                glow_radius = indicator_radius + glow * 3
                draw.ellipse(
                    [
                        indicator_x - glow_radius, indicator_y - glow_radius,
                        indicator_x + glow_radius, indicator_y + glow_radius,
                    ],
                    fill=primary_color + (30,),
                )

            draw.ellipse(
                [
                    indicator_x - indicator_radius, indicator_y - indicator_radius,
                    indicator_x + indicator_radius, indicator_y + indicator_radius,
                ],
                fill=(255, 255, 255, 255),
            )
        else:
            live_bar = Image.new("RGBA", (progress_width, progress_height + 20), (0, 0, 0, 0))
            live_draw = ImageDraw.Draw(live_bar)
            live_draw.rounded_rectangle(
                [(0, 10), (progress_width, 10 + progress_height)],
                radius=progress_height // 2,
                fill=(255, 40, 40, 220),
            )
            live_bar = live_bar.filter(ImageFilter.GaussianBlur(1))
            background.paste(live_bar, (progress_x, progress_y), live_bar)

        time_y = progress_y + 30
        draw_text_with_shadow(
            background, draw, (progress_x, time_y), "00:00", time_font,
            (200, 200, 240), shadow_offset=(1, 1), shadow_blur=2,
        )

        duration_display = "LIVE" if duration == "Live" else str(duration)
        duration_color = (255, 80, 80) if duration == "Live" else (200, 200, 240)
        draw_text_with_shadow(
            background, draw,
            (progress_x + progress_width - 80, time_y),
            duration_display, time_font, duration_color,
            shadow_offset=(1, 1), shadow_blur=2,
        )

        try:
            play_icons = Image.open("play_icons.png")
            icon_width = min(520, text_area_width - 40)
            play_icons = play_icons.resize((icon_width, int(62 * icon_width / 580)))
            icons_position = (progress_x + (progress_width - icon_width) // 2, time_y + 50)
            background.paste(play_icons, icons_position, play_icons)
        except Exception:
            play_y = time_y + 60
            play_x = progress_x + progress_width // 2
            draw.ellipse(
                [play_x - 30, play_y - 30, play_x + 30, play_y + 30],
                fill=(255, 255, 255, 200),
                outline=primary_color + (255,),
                width=3,
            )
            draw.polygon(
                [(play_x - 10, play_y - 15), (play_x - 10, play_y + 15), (play_x + 15, play_y)],
                fill=primary_color + (255,),
            )

        background = background.convert("RGB")
        background = background.resize((960, 540))
        background_path = f"cache/{random_id}_{videoid}_premium.png"
        background.save(background_path, "JPEG", quality=65, optimize=True, subsampling=1)

        for temp_file in temp_files_to_delete:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except Exception:
                pass

        return background_path

    except Exception as e:
        logger.error(
            f"Error generating thumbnail for video {videoid}: {type(e).__name__} - {e}",
            exc_info=True,
        )
        return None
