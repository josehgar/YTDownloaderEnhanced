import flet as ft
import yt_dlp
import os
import asyncio
import json


async def main(page: ft.Page) -> None:
    page.title = "TerminalYT Downloader"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#0a0a0a"
    page.padding = 30
    page.scroll = ft.ScrollMode.ADAPTIVE

    # Tipografía y colores temáticos
    GREEN_TERM = ft.Colors.GREEN_ACCENT_400
    DARK_GREY = "#1e1e1e"
    FONT_FAMILY = "JetBrains Mono, Consolas, Courier New, monospace"

    page.theme = ft.Theme(font_family=FONT_FAMILY)

    # Ruta de descarga actual
    current_download_path = os.getcwd()

    # FilePicker: en Flet 0.70+ es un servicio, no un control visual
    file_picker = ft.FilePicker()
    page.services.append(file_picker)

    def term_button_style() -> ft.ButtonStyle:
        return ft.ButtonStyle(
            color=GREEN_TERM,
            side=ft.BorderSide(1, GREEN_TERM),
            shape=ft.RoundedRectangleBorder(radius=2),
        )

    def show_snack(message: str, color=GREEN_TERM) -> None:
        """Muestra un SnackBar temático (se cierra solo)."""
        page.show_dialog(
            ft.SnackBar(
                content=ft.Text(message, color=color, font_family=FONT_FAMILY),
                bgcolor=DARK_GREY,
                behavior=ft.SnackBarBehavior.FLOATING,
                duration=4000,
            )
        )

    # Título principal
    header = ft.Text(
        ">_ YT-DLP TERMINAL INTERFACE v1.1",
        size=24,
        weight=ft.FontWeight.BOLD,
        color=GREEN_TERM,
    )

    search_input = ft.TextField(
        label="",
        hint_text="Ingresa el término de búsqueda...",
        expand=True,
        border_color=GREEN_TERM,
        color=GREEN_TERM,
        cursor_color=GREEN_TERM,
        focused_border_color=GREEN_TERM,
        text_style=ft.TextStyle(font_family=FONT_FAMILY),
    )

    search_button = ft.OutlinedButton(
        "EXECUTE",
        icon=ft.Icons.TERMINAL,
        style=term_button_style(),
    )

    selected_dir_text = ft.Text(
        f"[DIR] {current_download_path}",
        color=ft.Colors.GREY_400,
        font_family=FONT_FAMILY,
        size=12,
    )

    async def set_path(e):
        nonlocal current_download_path
        ruta_seleccionada = await file_picker.get_directory_path()
        if ruta_seleccionada:
            current_download_path = ruta_seleccionada
            selected_dir_text.value = f"[DIR] {current_download_path}"
            page.update()

    dir_button = ft.OutlinedButton(
        "SET_OUTPUT_DIR",
        icon=ft.Icons.FOLDER_OPEN,
        on_click=set_path,
        style=term_button_style(),
    )

    results_column = ft.Column(spacing=15)

    search_progress_row = ft.Row(
        [
            ft.ProgressRing(color=GREEN_TERM, width=20, height=20, stroke_width=2),
            ft.Text(
                "[SYSTEM] SEARCHING_YOUTUBE_DATABASE...",
                color=GREEN_TERM,
                font_family=FONT_FAMILY,
                weight=ft.FontWeight.BOLD,
            ),
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        visible=False,
    )

    async def download_audio(url: str, title: str, button: ft.OutlinedButton) -> None:
        # Todo el código de UI corre en el event loop de Flet (sin hilos propios);
        # solo la descarga bloqueante va a un hilo con asyncio.to_thread.
        download_dir = current_download_path

        button.disabled = True
        button.content = "[DOWNLOADING...]"
        button.icon = None

        # Diálogo modal nuevo en cada descarga (evita reutilizar uno ya "abierto")
        status_dialog = ft.AlertDialog(
            modal=True,
            bgcolor=DARK_GREY,
            title=ft.Row(
                [
                    ft.ProgressRing(color=GREEN_TERM),
                    ft.Container(width=15),
                    ft.Text(
                        "[PROCESSING] DOWNLOADING...",
                        size=18,
                        weight=ft.FontWeight.BOLD,
                        color=GREEN_TERM,
                        font_family=FONT_FAMILY,
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            content_padding=40,
        )
        page.show_dialog(status_dialog)
        page.update()

        def blocking_download() -> None:
            ydl_opts = {
                "format": "m4a/bestaudio/best",
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "m4a",
                }],
                "outtmpl": os.path.join(download_dir, "%(title)s.%(ext)s"),
                "quiet": True,
                "nocheckcertificate": True,
                "extractor_args": {"youtube": {"player_client": ["web", "ios", "android"]}},
                "legacyserverconnect": True,
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

        error = None
        try:
            await asyncio.to_thread(blocking_download)
        except Exception as ex:
            error = ex
            print(f"Error downloading {url}: {ex}")

        # Cerramos el diálogo de progreso y avisamos con el SnackBar
        page.pop_dialog()
        button.disabled = False

        if error is None:
            button.content = "[DOWNLOADED]"
            button.icon = ft.Icons.CHECK_CIRCLE_OUTLINE
            show_snack(f"[SUCCESS] '{title}' instalado en {download_dir}")
        else:
            button.content = "[ERROR]"
            show_snack(f"[ERROR] {error}", ft.Colors.RED_ACCENT)

        page.update()

    def build_card(index, title, uploader, url):
        download_btn = ft.OutlinedButton(
            "DOWNLOAD.m4a",
            icon=ft.Icons.DOWNLOAD,
            style=term_button_style(),
        )

        async def on_download(e):
            await download_audio(url, title, download_btn)

        download_btn.on_click = on_download

        link_btn = ft.TextButton(
            "BROWSER_LINK",
            icon=ft.Icons.OPEN_IN_BROWSER,
            url=url,
            style=ft.ButtonStyle(color=ft.Colors.BLUE_400),
        )

        return ft.Container(
            border=ft.Border.all(1, GREEN_TERM),
            border_radius=5,
            bgcolor=DARK_GREY,
            padding=15,
            content=ft.Column([
                ft.Text(
                    f"[{index}] {title}",
                    size=16,
                    weight=ft.FontWeight.BOLD,
                    color=GREEN_TERM,
                    font_family=FONT_FAMILY,
                ),
                ft.Text(
                    f"HOST: {uploader}",
                    size=14,
                    color=ft.Colors.GREY_400,
                    font_family=FONT_FAMILY,
                ),
                ft.Row([download_btn, link_btn], alignment=ft.MainAxisAlignment.END),
            ]),
        )

    async def search_click(e):
        query = search_input.value
        if not query:
            return

        results_column.controls.clear()
        search_progress_row.visible = True
        search_button.disabled = True
        page.update()

        try:
            ydl_opts = {
                "extract_flat": True,
                "quiet": True,
                "nocheckcertificate": True,
            }

            def blocking_search():
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    return ydl.extract_info(f"ytsearch5:{query}", download=False)

            info = await asyncio.to_thread(blocking_search)
            entries = info.get("entries", [])

            for index, entry in enumerate(entries):
                title = entry.get("title", "Sin_titulo")
                uploader = entry.get("uploader", "UNKNOWN_USER")
                url = entry.get("url", "")
                results_column.controls.append(build_card(index, title, uploader, url))

        except Exception as ex:
            results_column.controls.append(
                ft.Text(f"[FATAL_ERROR] {ex}", color=ft.Colors.RED_ACCENT, font_family=FONT_FAMILY)
            )
        finally:
            search_progress_row.visible = False
            search_button.disabled = False
            page.update()

    search_button.on_click = search_click
    search_input.on_submit = search_click

    page.add(
        header,
        ft.Divider(color=GREEN_TERM, height=30),
        ft.Row([dir_button, selected_dir_text], alignment=ft.MainAxisAlignment.START),
        ft.Row([search_input, search_button]),
        ft.Container(height=20),
        search_progress_row,
        results_column,
    )


if __name__ == "__main__":
    ft.run(main)