"""Ноутбук анализа выполняется заново, вывод совпадает с сохранённым."""

import copy
import unittest
from pathlib import Path

import nbformat
from nbclient import NotebookClient

NOTEBOOK = Path(__file__).resolve().parent.parent / 'notebooks' / 'kz-auto-market.ipynb'
EXPECTED = [
    'Строк: 39966, столбцов: 25',
    'Явных дубликатов: 23471',
    'Явных дубликатов после унификации: 52',
    'Пошаговый результат совпадает с cleaning.clean() и с сохранённым CSV',
    'Итог: 16437 строк, 19 столбцов',
    'Доля «Меркур Авто» в продажах рынка: 1.25%',
    'Доля «Меркур Авто» в выручке рынка: 2.21%',
    'Доля «Меркур Авто» в продажах премиум-сегмента: 6.62%',
    'Доля в продажах без удаления дубликатов: 1.25%',
]
SECTIONS = [
    '## 1. Загрузка и первичный осмотр данных',
    '## 2. Глубокая очистка и преобразование данных',
    '## 3. Исследовательский анализ рынка',
    '## 4. Анализ рынка и позиции «Меркур Авто»',
    '### 4.6 Сильные и слабые стороны и пути решения',
    '## 5. Общий вывод',
]


def text_outputs(nb: nbformat.NotebookNode) -> list[str]:
    """Текстовый вывод каждой кодовой ячейки без графиков."""
    result = []
    for cell in nb.cells:
        if cell.cell_type != 'code':
            continue
        texts = []
        for out in cell.outputs:
            if out.output_type == 'stream':
                texts.append(out.text)
            elif 'data' in out and 'image/png' not in out.data:
                texts.append(out.data.get('text/plain', ''))
        result.append(''.join(texts))
    return result


class AnalysisNotebookTest(unittest.TestCase):
    saved: nbformat.NotebookNode
    fresh: nbformat.NotebookNode

    @classmethod
    def setUpClass(cls) -> None:
        cls.saved = nbformat.read(NOTEBOOK, as_version=4)
        cls.fresh = copy.deepcopy(cls.saved)
        NotebookClient(
            cls.fresh,
            timeout=600,
            kernel_name='python3',
            record_timing=False,
            resources={'metadata': {'path': str(NOTEBOOK.parent)}},
        ).execute()

    def test_cells_executed_in_order_without_errors(self) -> None:
        code = [c for c in self.saved.cells if c.cell_type == 'code']
        self.assertEqual(
            [c.execution_count for c in code], list(range(1, len(code) + 1))
        )
        for cell in code:
            for out in cell.outputs:
                self.assertNotEqual(out.output_type, 'error', cell.source)
                self.assertNotEqual(out.get('name'), 'stderr', cell.source)

    def test_saved_outputs_match_fresh_run(self) -> None:
        self.assertEqual(text_outputs(self.saved), text_outputs(self.fresh))

    def test_sections_and_key_results(self) -> None:
        sources = [cell.source for cell in self.saved.cells]
        for section in SECTIONS:
            self.assertTrue(any(s.startswith(section) for s in sources), section)
        text = '\n'.join(sources + text_outputs(self.saved))
        for expected in EXPECTED:
            self.assertIn(expected, text)
        for marker in ('TODO', '/home/', '/Users/', 'C:\\'):
            self.assertNotIn(marker, text)


if __name__ == '__main__':
    unittest.main()
