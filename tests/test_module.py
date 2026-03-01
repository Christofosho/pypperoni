import ast
import unittest
from unittest.mock import patch, MagicMock
from io import StringIO

from app.module import (
    Module,
    PackageModule,
    NullModule,
    ExternalModule,
    BuiltinModule,
    write_modules_file,
)
from app.codeobj import CodeObject



# FakeContext simulates the Context class for testing Module logic without side effects.
class FakeContext:
    def __init__(self):
        self.lines = []  # Tracks lines inserted by handle_op and related methods
        self.blocks = 0  # Simulates block stack depth
        self.i = 0       # Instruction pointer for chunk processing
        self.buf = ()    # Buffer of instructions
        self.codeobjs = []  # List of code objects (if needed)
        self.file = None
        self._consts = []
        self.labels_inserted = []  # Tracks inserted labels
        self.decls = {}  # Tracks declared variables
        self.yields = [] # Tracks yield points
        self.errors = [] # Tracks error handling insertions
        self.finished = False
        self.consts_flushed = False

    def insert_line(self, line):
        self.lines.append(line)

    def begin_block(self):
        self.blocks += 1

    def end_block(self):
        self.blocks -= 1

    def insert_label(self, label):
        self.labels_inserted.append(label)

    def insert_handle_error(self, line, label):
        self.errors.append((line, label))
        self.insert_line(f'/* error handle at label {label} line {line} */')

    def add_decl_once(self, name, ctype, init, unused):
        self.decls[name] = (ctype, init)

    def register_const(self, value):
        return f'const_{id(value)}'

    def register_literal(self, value):
        return f'literal_{id(value)}'

    def insert_get_address(self, addr):
        self.insert_line(f'__addr = (void*){addr};')

    def insert_yield(self, line, label):
        self.yields.append((line, label))
        self.insert_line(f'/* yield at {label} line {line} */')

    def finish(self, multi_chunk):
        self.finished = True

    def flushconsts(self):
        self.consts_flushed = True



# FakeFile simulates a file-like object for capturing output and headers in tests.
class FakeFile:
    def __init__(self):
        self.buffer = StringIO()
        self.headers = []
        self.uid = 'test_uid'
        self.closed = False
        self.mode = 'w'
        self.name = 'fakefile.c'

    def write(self, text):
        self.buffer.write(text)

    def add_common_header(self, header):
        self.headers.append(header)

    def get_output(self):
        return self.buffer.getvalue()

    def close(self):
        self.closed = True

    def flush(self):
        pass


class TestModuleGetParent(unittest.TestCase):
    def test_get_parent_with_dotted_name(self):
        parent_mod = Module('parent', '')
        child_mod = Module('parent.child', '')
        modules = {'parent': parent_mod, 'parent.child': child_mod}

        result = child_mod.get_parent(modules)
        self.assertEqual(result, parent_mod)

    def test_get_parent_with_non_dotted_name(self):
        mod = Module('simple', '')
        result = mod.get_parent({})
        self.assertIsNone(result)

    def test_get_parent_missing_parent(self):
        child_mod = Module('parent.child', '')
        result = child_mod.get_parent({})
        self.assertIsNone(result)


class TestModuleGetContext(unittest.TestCase):
    def test_get_context_returns_context_instance(self):
        mod = Module('test', '')
        fake_file = FakeFile()
        modules = {}

        from app.context import Context
        context = mod.get_context(fake_file, 'test_context', modules, 0, 5)

        self.assertIsInstance(context, Context)


class TestModuleGetCode(unittest.TestCase):
    def test_get_code_returns_codeobject(self):
        code_str = "x = 1\ny = 2"
        mod = Module('test', code_str)

        code = mod.get_code()

        self.assertIsInstance(code, CodeObject)


class TestModuleHandleOp(unittest.TestCase):
    def test_handle_op_nop(self):
        from opcode import opmap
        mod = Module('test', '')
        context = FakeContext()
        codeobj = MagicMock()
        codeobj.configure_mock(co_varnames=(), co_names=(), co_consts=())
        mod.handle_op(codeobj, context, 0, opmap['NOP'], 0, 1)
        self.assertEqual(context.lines, ['/* NOP */'])

    def test_handle_op_pop_top(self):
        from opcode import opmap
        mod = Module('test', '')
        context = FakeContext()
        codeobj = MagicMock()
        codeobj.configure_mock(co_varnames=(), co_names=(), co_consts=())
        mod.handle_op(codeobj, context, 0, opmap['POP_TOP'], 0, 1)
        self.assertEqual(context.blocks, 0)
        self.assertEqual(context.lines, ['v = POP();', 'Py_DECREF(v);'])


class TestModuleHandleOneInstr(unittest.TestCase):
    def test_handle_one_instr_calls_insert_label_and_handle_op(self):
        from opcode import opmap
        mod = Module('test', '')
        context = FakeContext()
        codeobj = MagicMock()
        codeobj.configure_mock(co_varnames=(), co_names=(), co_consts=())
        with patch.object(mod, 'handle_op') as mock_handle_op:
            mod._Module__handle_one_instr(codeobj, context, 10, opmap['NOP'], 0, 5)
            self.assertEqual(context.labels_inserted, [10])
            mock_handle_op.assert_called_once_with(codeobj, context, 10, opmap['NOP'], 0, 5)


class TestModuleHandleChunk(unittest.TestCase):
    def test_handle_chunk_processes_instructions(self):
        from opcode import opmap
        mod = Module('test', '')
        fake_file = FakeFile()
        modules = {}
        fake_context = FakeContext()
        chunk = [
            (0, opmap['NOP'], 0, 1),
            (2, opmap['NOP'], 0, 1),
        ]
        codeobj = MagicMock()
        codeobj.co_flags = 0
        codeobj.co_nlocals = 0
        codeobj.co_varnames = ()
        codeobj.co_names = ()
        codeobj.co_consts = ()
        with patch.object(mod, 'get_context', return_value=fake_context):
            context = mod._Module__handle_chunk(chunk, fake_file, 'test_chunk', modules, codeobj, [], [])
        self.assertIsNotNone(context)
        self.assertEqual(fake_context.labels_inserted, [0, 2])
        self.assertEqual(fake_context.lines, ['/* NOP */', '/* NOP */'])


class TestModuleSplitBuf(unittest.TestCase):
    def test_split_buf_with_generator(self):
        from opcode import opmap
        from app.util import CO_GENERATOR
        mod = Module('test', 'yield 1')
        buf = [(0, opmap['NOP'], 0, 1)]
        codeobj = MagicMock()
        codeobj.configure_mock(co_flags=CO_GENERATOR)
        chunks = list(mod._Module__split_buf(buf, codeobj))
        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0], buf)


class TestModuleConvertRelativeImport(unittest.TestCase):
    def test_convert_relative_import_absolute(self):
        mod = Module('mymodule', '')
        result = mod._Module__convert_relative_import('name', 0)

        self.assertEqual(result, 'name')

    def test_convert_relative_import_relative_from_package(self):
        mod = PackageModule('parent.child', '')
        result = mod._Module__convert_relative_import('sibling', 1)

        self.assertEqual(result, 'parent.child.sibling')

        result = mod._Module__convert_relative_import('name', 2)

        self.assertEqual(result, 'parent.name')

        with self.assertRaises(ImportError):
            mod._Module__convert_relative_import('name', 3)


class TestModuleResolveImportFromName(unittest.TestCase):

    def test_resolve_import_from_name_existing_module(self):
        existing = Module('os', '')
        modules = {'os': existing}

        mod = Module('test', '')
        result = mod.resolve_import_from_name(modules, 'os')

        self.assertEqual(result, existing)

    def test_resolve_import_from_name_missing_external_disabled(self):
        mod = Module('test', '')

        result = mod.resolve_import_from_name({}, 'missing', can_be_external=False)

        self.assertIsNone(result)


class TestModuleResolveImportsFromNode(unittest.TestCase):
    def test_resolve_imports_from_node(self):
        os_mod = Module('os', '')
        modules = {'os': os_mod}

        mod = Module('test', '')
        code = "import os"
        tree = ast.parse(code)
        import_node = tree.body[0]

        results = list(mod.resolve_imports_from_node(modules, import_node))

        self.assertIn(os_mod, results)

    def test_resolve_imports_from_node_from_import(self):
        os_mod = Module('os', '')
        modules = {'os': os_mod}

        mod = Module('test', '')
        code = "from os import path"
        tree = ast.parse(code)
        import_node = tree.body[0]

        results = list(mod.resolve_imports_from_node(modules, import_node))

        self.assertIn(os_mod, results)


class TestModuleLookupImport(unittest.TestCase):
    def test_lookup_import_in_modules(self):
        existing = Module('os', '')
        modules = {'os': existing}

        mod = Module('test', '')
        result = mod._Module__lookup_import('os', modules)

        self.assertEqual(result, 'os')

    def test_lookup_import_builtin_module(self):
        modules = {}

        mod = Module('test', '')
        result = mod._Module__lookup_import('sys', modules, can_be_external=True)

        self.assertEqual(result, 'sys')
        self.assertIn('sys', modules)
        self.assertIsInstance(modules['sys'], BuiltinModule)

    def test_lookup_import_external_module(self):
        modules = {}

        mod = Module('test', '')
        with patch('builtins.__import__', side_effect=ImportError):
            result = mod._Module__lookup_import('nonexistent_mod_12345', modules, 
                                                can_be_external=True)

        self.assertEqual(result, 'nonexistent_mod_12345')
        self.assertIn('nonexistent_mod_12345', modules)
        self.assertIsInstance(modules['nonexistent_mod_12345'], ExternalModule)


class TestPackageModule(unittest.TestCase):
    def test_package_module_is_package(self):
        mod = PackageModule('mypackage', '')
        self.assertTrue(mod.is_package())


class TestNullModule(unittest.TestCase):
    def test_null_module_init(self):
        mod = NullModule('empty')

        self.assertEqual(mod.name, 'empty')
        self.assertIsNotNone(mod.astmod)


class TestExternalModule(unittest.TestCase):
    def test_external_module_is_external(self):
        mod = ExternalModule('external')
        self.assertTrue(mod.is_external())


class TestBuiltinModule(unittest.TestCase):
    def test_builtin_module_is_external(self):
        mod = BuiltinModule('sys')
        self.assertTrue(mod.is_external())


class TestWriteModulesFile(unittest.TestCase):
    def _required_modules(self):
        encodings_mod = Module('encodings', '')
        encodings_mod.code = encodings_mod.get_code()
        codecs_index_mod = Module('codecs_index', '')
        codecs_index_mod.code = codecs_index_mod.get_code()
        return {
            'encodings': encodings_mod,
            'codecs_index': codecs_index_mod,
        }

    def test_write_modules_file_with_defined_module(self):
        fake_file = FakeFile()

        defined_mod = Module('defined', 'x = 1')
        defined_mod.code = defined_mod.get_code()

        modules = {'defined': defined_mod, **self._required_modules()}

        write_modules_file(fake_file, modules)

        output = fake_file.get_output()
        self.assertIn('m->name = "defined";', output)
        self.assertIn('m->type = MODULE_DEFINED;', output)
        self.assertIn('PyObject* _defined_MODULE__(PyFrameObject* f); /* fwd decl */', output)

    def test_write_modules_file_with_external_module(self):
        fake_file = FakeFile()

        external_mod = ExternalModule('external')

        modules = {'external': external_mod, **self._required_modules()}

        write_modules_file(fake_file, modules)

        output = fake_file.get_output()
        self.assertIn('m->name = "external";', output)
        self.assertIn('m->type = MODULE_BUILTIN;', output)
        self.assertIn('m->stacksize = 0;', output)
        self.assertIn('m->nlocals = 0;', output)
        self.assertNotIn('PyObject* _external_MODULE__(PyFrameObject* f); /* fwd decl */', output)

    def test_write_modules_file_stacksize_nlocals(self):
        fake_file = FakeFile()

        mod = Module('test', 'pass')
        mod.code = mod.get_code()
        modules = {'test': mod, **self._required_modules()}

        write_modules_file(fake_file, modules)

        output = fake_file.get_output()
        self.assertIn(f'm->stacksize = {mod.code.co_stacksize};', output)
        self.assertIn(f'm->nlocals = {mod.code.co_nlocals};', output)


class TestModuleGenerateCCode(unittest.TestCase):
    def test_generate_c_code_calls_gen_code(self):
        mod = Module('mymodule', 'x = 1')
        fake_file = FakeFile()
        modules = {}

        with patch.object(mod, '_Module__gen_code') as mock_gen:
            mod.generate_c_code(fake_file, modules)

            mock_gen.assert_called_once()
            call_args = mock_gen.call_args

            self.assertEqual(call_args[0][0], fake_file)
            self.assertIn('mymodule', call_args[0][1])
            self.assertEqual(call_args[0][2], modules)


if __name__ == '__main__':
    unittest.main()
