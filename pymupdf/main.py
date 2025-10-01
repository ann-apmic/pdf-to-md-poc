#!/usr/bin/env python3
"""
PyMuPDF 測試腳本

這個腳本用於測試 PyMuPDF 套件的基本功能，
將 PDF 文件轉換為 Markdown 格式。

使用方法:
    python main.py
"""

import sys
from pathlib import Path

import pymupdf as fitz  # PyMuPDF

# ==================== 配置常數 ====================

# 輸出目錄設定
OUTPUT_DIR_NAME = "output"         # 輸出目錄名稱

# PyMuPDF 設定
# 文字提取模式: "text", "blocks", "dict", "html", "xhtml", "xml"
TEXT_EXTRACTION_MODE = "text"

# 支援的文件格式 (PyMuPDF 主要用於 PDF)
SUPPORTED_EXTENSIONS = {
    '.pdf',  # PyMuPDF 主要支援 PDF
}

# 文件編碼
FILE_ENCODING = 'utf-8'

# 檔案大小限制 (單位: MB)
MAX_FILE_SIZE_MB = 50  # 超過此大小的檔案將被跳過

# 來源設定 - 支援資料夾、單獨檔案
SOURCES = [
    {
        "type": "folder",           # 來源類型: "folder", "file"
        "path": "_testing-files/pdf",   # 路徑
        "name": "測試檔案目錄",     # 顯示名稱
        "recursive": True          # 是否遞歸處理子目錄 (只對 folder 有效)
    },
    # 示例：單獨檔案
    # {
    #     "type": "file",
    #     "path": "../_testing-files/pdf/sample.pdf",
    #     "name": "單獨PDF檔案"
    # },
]

# ==================== 配置常數結束 ====================


def setup_output_directory():
    """設定輸出目錄"""
    output_dir = Path("pymupdf") / OUTPUT_DIR_NAME
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"📁 輸出目錄: {output_dir.absolute()}")
    return output_dir


def setup_pymupdf():
    """設定 PyMuPDF 實例"""
    try:
        # PyMuPDF 不需要特別的實例創建，直接使用模組
        print("✅ PyMuPDF 模組載入成功")
        return fitz
    except Exception as e:
        print(f"❌ 無法載入 PyMuPDF 模組: {e}")
        sys.exit(1)


def extract_text_from_pdf(pdf_path: str, mode: str = "text") -> str:
    """從 PDF 文件提取文字"""
    try:
        # 開啟 PDF 文件
        doc = fitz.open(pdf_path)

        text_content = []

        # 遍歷每一頁
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)

            if mode == "text":
                # 簡單文字提取
                text = page.get_text()
            elif mode == "blocks":
                # 以區塊方式提取
                blocks = page.get_text("blocks")
                text = "\n".join([block[4] for block in blocks
                                  if block[4].strip()])
            elif mode == "dict":
                # 以字典方式提取
                text_dict = page.get_text("dict")
                text = ""
                for block in text_dict.get("blocks", []):
                    if block.get("type") == 0:  # 文字區塊
                        for line in block.get("lines", []):
                            for span in line.get("spans", []):
                                text += span.get("text", "") + " "
                            text += "\n"
                        text += "\n"
            else:
                # 其他模式使用預設
                text = page.get_text(mode)

            if text.strip():
                text_content.append(f"## 頁面 {page_num + 1}\n\n{text.strip()}")

        doc.close()

        # 以 Markdown 格式組合內容
        if text_content:
            full_content = "# PDF 內容提取\n\n" + "\n\n".join(text_content)
        else:
            full_content = "# PDF 內容提取\n\n*無法提取文字內容*"

        return full_content

    except Exception as e:
        raise Exception(f"PDF 文字提取失敗: {e}")


def process_folder_source(fitz_module,
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
                # 使用 PyMuPDF 提取文字
                markdown_content = extract_text_from_pdf(
                    str(file_path), TEXT_EXTRACTION_MODE)

                # 創建對應的輸出目錄結構
                relative_path = file_path.relative_to(folder_path)
                output_file_path = (output_dir / source_name /
                                    relative_path.with_suffix('.md'))

                # 確保輸出目錄存在
                output_file_path.parent.mkdir(parents=True, exist_ok=True)

                # 保存轉換結果
                with open(output_file_path, 'w', encoding=FILE_ENCODING) as f:
                    f.write(markdown_content)

                print("✅ 轉換成功")
                print(f"📄 輸入大小: {file_path.stat().st_size} bytes")
                print(f"📂 輸出位置: {output_file_path}")

                # 顯示內容統計
                content = markdown_content.strip()
                if content:
                    print(f"📊 內容長度: {len(markdown_content)} 字符")
                else:
                    print("📊 內容: 空")

                converted_count += 1

            except Exception as e:
                print(f"❌ 轉換失敗: {e}")
                failed_count += 1

    return converted_count, failed_count, skipped_count


def process_file_source(fitz_module, source_config: dict, output_dir: Path):
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
        # 檢查檔案大小
        file_size_mb = file_path.stat().st_size / (1024 * 1024)
        if file_size_mb > MAX_FILE_SIZE_MB:
            print(f"--- 跳過大檔案: {file_path.name} ---")
            print(f"📄 檔案大小: {file_size_mb:.1f} MB "
                  f"(超過限制 {MAX_FILE_SIZE_MB} MB)")
            return 0, 0, 1  # 跳過計數 +1

        # 使用 PyMuPDF 提取文字
        markdown_content = extract_text_from_pdf(
            str(file_path), TEXT_EXTRACTION_MODE)

        # 創建輸出檔案路徑
        output_file_path = (output_dir / "single_files" /
                            f"{source_name}.md")

        # 確保輸出目錄存在
        output_file_path.parent.mkdir(parents=True, exist_ok=True)

        # 保存轉換結果
        with open(output_file_path, 'w', encoding=FILE_ENCODING) as f:
            f.write(markdown_content)

        print("✅ 轉換成功")
        print(f"📄 輸入大小: {file_path.stat().st_size} bytes")
        print(f"📂 輸出位置: {output_file_path}")

        # 顯示內容統計
        content = markdown_content.strip()
        if content:
            print(f"📊 內容長度: {len(markdown_content)} 字符")
        else:
            print("📊 內容: 空")

        return 1, 0, 0  # 成功計數 +1

    except Exception as e:
        print(f"❌ 轉換失敗: {e}")
        return 0, 1, 0  # 失敗計數 +1


def convert_from_sources(fitz_module, sources: list, output_dir: Path):
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
                fitz_module, source_config, output_dir)
        elif source_type == "file":
            converted, failed, skipped = process_file_source(
                fitz_module, source_config, output_dir)
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
    print("🚀 PyMuPDF PDF 轉 Markdown 腳本開始")
    print("=" * 50)

    # 檢查來源配置
    if not SOURCES:
        print("❌ 未配置任何來源，請在 SOURCES 變數中添加來源配置")
        sys.exit(1)

    # 設定輸出目錄
    output_dir = setup_output_directory()

    # 設定 PyMuPDF
    fitz_module = setup_pymupdf()

    # 從配置的來源轉換所有文件
    result = convert_from_sources(fitz_module, SOURCES, output_dir)
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
    print(f"   - 使用文字提取模式: {TEXT_EXTRACTION_MODE}")


if __name__ == "__main__":
    main()
