#!/usr/bin/env python3
"""
MarkItDown 測試腳本

這個腳本用於測試 MarkItDown 套件的基本功能，
將各種文件格式轉換為 Markdown 格式。

使用方法:
    python test_markitdown.py
"""

import sys
from pathlib import Path

from markitdown import MarkItDown

# ==================== 配置常數 ====================

# 輸出目錄設定
OUTPUT_DIR_NAME = "output"         # 輸出目錄名稱

# MarkItDown 設定
ENABLE_PLUGINS = False  # 是否啟用插件

# 支援的文件格式
SUPPORTED_EXTENSIONS = {
    # 文檔格式
    '.pdf', '.docx', '.xlsx', '.xls', '.txt', '.csv', '.html', '.htm',
    '.epub', '.rtf', '.odt',

    # 圖片格式
    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff',

    # 音頻格式
    '.wav', '.mp3', '.m4a',

    # 視頻格式
    '.mp4', '.mov', '.avi'
}

# 文件編碼
FILE_ENCODING = 'utf-8'

# 檔案大小限制 (單位: MB)
MAX_FILE_SIZE_MB = 50  # 超過此大小的檔案將被跳過

# 來源設定 - 支援資料夾、單獨檔案和 URL
SOURCES = [
    {
        "type": "folder",           # 來源類型: "folder", "file", "url"
        "path": "_testing-files/pdf",   # 路徑或URL
        "name": "測試檔案目錄",     # 顯示名稱
        "recursive": True          # 是否遞歸處理子目錄 (只對 folder 有效)
    },
    {
        "type": "folder",
        "path": "_testing-files/html",
        "name": "html",
    },
    # 示例：單獨檔案
    {
        "type": "file",
        "path": "_testing-files/sample.csv",
        "name": "單獨文字檔案"
    },
    # 示例：URL (注意：需要網路連線)
    # {
    #     "type": "url",
    #     "path": "https://example.com",
    #     "name": "範例網站"
    # },
    # 示例：另一個資料夾 (取消註釋並修改路徑以使用)
    # {
    #     "type": "folder",
    #     "path": "another-folder",
    #     "name": "其他檔案",
    #     "recursive": False  # 不遞歸，只處理頂層檔案
    # }
]

# ==================== 配置常數結束 ====================


def setup_output_directory():
    """設定輸出目錄"""
    output_dir = Path("markitdown") / OUTPUT_DIR_NAME
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"📁 輸出目錄: {output_dir.absolute()}")
    return output_dir


def setup_markitdown():
    """設定 MarkItDown 實例"""
    try:
        # 創建 MarkItDown 實例
        md = MarkItDown(enable_plugins=ENABLE_PLUGINS)
        print("✅ MarkItDown 實例創建成功")
        return md
    except Exception as e:
        print(f"❌ 無法創建 MarkItDown 實例: {e}")
        sys.exit(1)


def process_folder_source(md: MarkItDown,
                          source_config: dict,
                          output_dir: Path):
    """處理資料夾來源"""
    folder_path = Path(source_config["path"])
    source_name = source_config.get("name", folder_path.name)
    recursive = source_config.get("recursive", True)

    print(f"\n📁 處理資料夾來源: {source_name} ({folder_path})")

    if not folder_path.exists():
        print(f"❌ 資料夾不存在: {folder_path}")
        return 0, 0, 0

    converted_count = 0
    failed_count = 0
    skipped_count = 0

    # 選擇遍歷方法
    if recursive:
        file_iterator = folder_path.rglob('*')
    else:
        file_iterator = folder_path.glob('*')

    # 處理每個檔案
    for file_path in file_iterator:
        if (file_path.is_file() and
                file_path.suffix.lower() in SUPPORTED_EXTENSIONS):

            # 檢查檔案大小
            file_size_mb = file_path.stat().st_size / (1024 * 1024)
            if file_size_mb > MAX_FILE_SIZE_MB:
                print(f"\n--- 跳過大檔案: {file_path.relative_to(folder_path)} ---")
                size_info = (
                    f"📄 檔案大小: {file_size_mb:.1f} MB "
                    f"(超過限制 {MAX_FILE_SIZE_MB} MB)"
                )
                print(size_info)
                skipped_count += 1
                continue

            print(f"\n--- 轉換文件: {file_path.relative_to(folder_path)} ---")

            try:
                # 轉換文件
                result = md.convert(str(file_path))

                # 創建對應的輸出目錄結構
                relative_path = file_path.relative_to(folder_path)
                output_file_path = (output_dir / source_name /
                                    relative_path.with_suffix('.md'))

                # 確保輸出目錄存在
                output_file_path.parent.mkdir(parents=True, exist_ok=True)

                # 保存轉換結果
                with open(output_file_path, 'w', encoding=FILE_ENCODING) as f:
                    f.write(result.text_content)

                print("✅ 轉換成功")
                print(f"📄 輸入大小: {file_path.stat().st_size} bytes")
                print(f"📂 輸出位置: {output_file_path}")

                # 顯示內容統計
                content = result.text_content.strip()
                if content:
                    print(f"📊 內容長度: {len(result.text_content)} 字符")
                else:
                    print("📊 內容: 空")

                converted_count += 1

            except Exception as e:
                print(f"❌ 轉換失敗: {e}")
                failed_count += 1

    return converted_count, failed_count, skipped_count


def process_file_source(md: MarkItDown, source_config: dict, output_dir: Path):
    """處理單獨檔案來源"""
    file_path = Path(source_config["path"])
    source_name = source_config.get("name", file_path.stem)

    print(f"\n📄 處理檔案來源: {source_name} ({file_path})")

    if not file_path.exists():
        print(f"❌ 檔案不存在: {file_path}")
        return 0, 1, 0  # 失敗計數 +1

    # 檢查檔案類型
    if file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        print(f"⚠️  不支援的檔案格式: {file_path.suffix}")
        return 0, 1, 0  # 失敗計數 +1

    print(f"\n--- 轉換文件: {file_path.name} ---")

    try:
        # 使用 open() 以二進制模式讀取檔案
        with open(file_path, 'rb') as f:
            file_bytes = f.read()

        # 檢查檔案大小（使用實際讀取的檔案大小）
        file_size_mb = len(file_bytes) / (1024 * 1024)
        if file_size_mb > MAX_FILE_SIZE_MB:
            print(f"--- 跳過大檔案: {file_path.name} ---")
            print(f"📄 檔案大小: {file_size_mb:.1f} MB "
                  f"(超過限制 {MAX_FILE_SIZE_MB} MB)")
            return 0, 0, 1  # 跳過計數 +1

        # 使用 BytesIO 將 bytes 數據包裝成檔案對象
        from io import BytesIO
        bio = BytesIO(file_bytes)
        bio.name = str(file_path)  # 設置檔案名

        # 使用 bytes 數據進行轉換
        result = md.convert(bio)

        # 創建輸出檔案路徑
        output_file_path = (output_dir / "single_files" /
                            f"{source_name}.md")

        # 確保輸出目錄存在
        output_file_path.parent.mkdir(parents=True, exist_ok=True)

        # 保存轉換結果
        with open(output_file_path, 'w', encoding=FILE_ENCODING) as f:
            f.write(result.text_content)

        print("✅ 轉換成功")
        print(f"📄 輸入大小: {len(file_bytes)} bytes")
        print(f"📂 輸出位置: {output_file_path}")

        # 顯示內容統計
        content = result.text_content.strip()
        if content:
            print(f"📊 內容長度: {len(result.text_content)} 字符")
        else:
            print("📊 內容: 空")

        return 1, 0, 0  # 成功計數 +1

    except Exception as e:
        print(f"❌ 轉換失敗: {e}")
        return 0, 1, 0  # 失敗計數 +1


def process_url_source(md: MarkItDown, source_config: dict, output_dir: Path):
    """處理 URL 來源"""
    url = source_config["path"]
    source_name = source_config.get("name", "web_content")

    print(f"\n🌐 處理 URL 來源: {source_name} ({url})")

    try:
        # 轉換 URL
        result = md.convert(url)

        # 創建輸出檔案路徑
        output_file_path = (output_dir / "urls" /
                            f"{source_name}.md")

        # 確保輸出目錄存在
        output_file_path.parent.mkdir(parents=True, exist_ok=True)

        # 保存轉換結果
        with open(output_file_path, 'w', encoding=FILE_ENCODING) as f:
            f.write(result.text_content)

        print("✅ 轉換成功")
        print(f"📂 輸出位置: {output_file_path}")

        # 顯示內容統計
        content = result.text_content.strip()
        if content:
            print(f"📊 內容長度: {len(result.text_content)} 字符")
        else:
            print("📊 內容: 空")

        return 1, 0, 0  # 成功計數 +1

    except Exception as e:
        print(f"❌ 轉換失敗: {e}")
        return 0, 1, 0  # 失敗計數 +1


def convert_from_sources(md: MarkItDown, sources: list, output_dir: Path):
    """從配置的來源轉換所有文件"""
    print(f"\n🔄 開始從 {len(sources)} 個來源轉換文件")

    total_converted = 0
    total_failed = 0
    total_skipped = 0

    for source_config in sources:
        source_type = source_config.get("type")
        source_name = source_config.get("name", "未命名來源")

        separator = '=' * 20
        print(f"\n{separator} 處理來源: {source_name} ({source_type}) {separator}")

        if source_type == "folder":
            converted, failed, skipped = process_folder_source(
                md, source_config, output_dir)
        elif source_type == "file":
            converted, failed, skipped = process_file_source(
                md, source_config, output_dir)
        elif source_type == "url":
            converted, failed, skipped = process_url_source(
                md, source_config, output_dir)
        else:
            print(f"❌ 不支援的來源類型: {source_type}")
            continue

        total_converted += converted
        total_failed += failed
        total_skipped += skipped

        print(f"來源 {source_name} 處理完成: ✅{converted} ❌{failed} ⏭️{skipped}")

    print("\n📈 總體轉換總結:")
    print(f"   ✅ 成功: {total_converted} 個文件")
    print(f"   ❌ 失敗: {total_failed} 個文件")
    print(f"   ⏭️  跳過: {total_skipped} 個文件 (檔案過大)")

    return total_converted, total_failed, total_skipped


def main():
    """主函數"""
    print("🚀 MarkItDown 批量轉換腳本開始")
    print("=" * 50)

    # 檢查來源配置
    if not SOURCES:
        print("❌ 未配置任何來源，請在 SOURCES 變數中添加來源配置")
        sys.exit(1)

    # 設定輸出目錄
    output_dir = setup_output_directory()

    # 設定 MarkItDown
    md = setup_markitdown()

    # 從配置的來源轉換所有文件
    result = convert_from_sources(md, SOURCES, output_dir)
    converted_count, failed_count, skipped_count = result

    print("\n" + "=" * 50)
    print("🎉 批量轉換完成！")
    total_processed = converted_count + failed_count + skipped_count
    print(f"📊 總計處理: {total_processed} 個文件")
    print(f"   ✅ 成功轉換: {converted_count} 個文件")
    print(f"   ❌ 轉換失敗: {failed_count} 個文件")
    print(f"   ⏭️  跳過檔案: {skipped_count} 個文件 (檔案過大)")
    print(f"\n💡 輸出目錄: {output_dir.absolute()}")
    print("   - 所有 Markdown 文件已按來源類型組織保存")
    print("   - 如需啟用插件，請修改腳本中的 ENABLE_PLUGINS 參數")
    print("   - 如需使用 Azure Document Intelligence，請提供 docintel_endpoint 參數")


if __name__ == "__main__":
    main()
