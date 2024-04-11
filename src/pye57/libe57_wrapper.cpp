
#include <pybind11/pybind11.h>
#include <pybind11/stl_bind.h>
#include <pybind11/numpy.h>

#include <E57Exception.h>
#include <E57Format.h>
#include <E57Version.h>
#include <ASTMVersion.h>

namespace py = pybind11;
using namespace pybind11::literals;

using namespace e57;

PYBIND11_MAKE_OPAQUE(std::vector<SourceDestBuffer>);

auto cast_node (Node &n) {
    NodeType type = n.type();
    if (type == NodeType::E57_BLOB)
        return py::cast(BlobNode(n));
    else if (type == NodeType::E57_COMPRESSED_VECTOR)
        return py::cast(CompressedVectorNode(n));
    else if (type == NodeType::E57_FLOAT)
        return py::cast(FloatNode(n));
    else if (type == NodeType::E57_INTEGER)
        return py::cast(IntegerNode(n));
    else if (type == NodeType::E57_SCALED_INTEGER)
        return py::cast(ScaledIntegerNode(n));
    else if (type == NodeType::E57_STRING)
        return py::cast(StringNode(n));
    else if (type == NodeType::E57_STRUCTURE)
        return py::cast(StructureNode(n));
    else if (type == NodeType::E57_VECTOR)
        return py::cast(VectorNode(n));
}

PYBIND11_MODULE(libe57, m) {
    m.doc() = "E57 reader/writer for python.";

    static py::exception<E57Exception> exc(m, "E57Exception");
    py::register_exception_translator([](std::exception_ptr p) {
    try {
        if (p) std::rethrow_exception(p);
    } catch (const E57Exception &e) {
        exc(Utilities::errorCodeToString(e.errorCode()).c_str());
    }
    });

    m.attr("E57_FORMAT_MAJOR") = E57_FORMAT_MAJOR;
    m.attr("E57_FORMAT_MINOR") = E57_FORMAT_MINOR;
    m.attr("E57_LIBRARY_ID") = REVISION_ID;
    m.attr("E57_V1_0_URI") = "http://www.astm.org/COMMIT/E57/2010-e57-v1.0";
    m.attr("CHECKSUM_POLICY_NONE") = CHECKSUM_POLICY_NONE;
    m.attr("CHECKSUM_POLICY_SPARSE") = CHECKSUM_POLICY_SPARSE;
    m.attr("CHECKSUM_POLICY_HALF") = CHECKSUM_POLICY_HALF;
    m.attr("CHECKSUM_POLICY_ALL") = CHECKSUM_POLICY_ALL;
    m.attr("E57_INT8_MIN") = INT8_MIN;
    // for some reason INT8_MAX casts to a string not to an int !
    m.attr("E57_INT8_MAX") = 127;
    m.attr("E57_INT16_MIN") = INT16_MIN;
    m.attr("E57_INT16_MAX") = INT16_MAX;
    m.attr("E57_INT32_MIN") = INT32_MIN;
    m.attr("E57_INT32_MAX") = INT32_MAX;
    m.attr("E57_INT64_MIN") = INT64_MIN;
    m.attr("E57_INT64_MAX") = INT64_MAX;
    m.attr("E57_UINT8_MIN") = UINT8_MIN;
    m.attr("E57_UINT8_MAX") = UINT8_MAX;
    m.attr("E57_UINT16_MIN") = UINT16_MIN;
    m.attr("E57_UINT16_MAX") = UINT16_MAX;
    m.attr("E57_UINT32_MIN") = UINT32_MIN;
    m.attr("E57_UINT32_MAX") = UINT32_MAX;
    m.attr("E57_UINT64_MIN") = UINT64_MIN;
    m.attr("E57_UINT64_MAX") = UINT64_MAX;
    m.attr("E57_FLOAT_MIN") = FLOAT_MIN;
    m.attr("E57_FLOAT_MAX") = FLOAT_MAX;
    m.attr("E57_DOUBLE_MIN") = DOUBLE_MIN;
    m.attr("E57_DOUBLE_MAX") = DOUBLE_MAX;
    py::enum_<NodeType>(m, "NodeType")
        .value("E57_STRUCTURE", NodeType::E57_STRUCTURE)
        .value("E57_VECTOR", NodeType::E57_VECTOR)
        .value("E57_COMPRESSED_VECTOR", NodeType::E57_COMPRESSED_VECTOR)
        .value("E57_INTEGER", NodeType::E57_INTEGER)
        .value("E57_SCALED_INTEGER", NodeType::E57_SCALED_INTEGER)
        .value("E57_FLOAT", NodeType::E57_FLOAT)
        .value("E57_STRING", NodeType::E57_STRING)
        .value("E57_BLOB", NodeType::E57_BLOB)
        .export_values();
    py::enum_<FloatPrecision>(m, "FloatPrecision")
        .value("E57_SINGLE", FloatPrecision::E57_SINGLE)
        .value("E57_DOUBLE", FloatPrecision::E57_DOUBLE)
        .export_values();
    py::enum_<MemoryRepresentation>(m, "MemoryRepresentation")
        .value("E57_INT8", MemoryRepresentation::E57_INT8)
        .value("E57_UINT8", MemoryRepresentation::E57_UINT8)
        .value("E57_INT16", MemoryRepresentation::E57_INT16)
        .value("E57_UINT16", MemoryRepresentation::E57_UINT16)
        .value("E57_INT32", MemoryRepresentation::E57_INT32)
        .value("E57_UINT32", MemoryRepresentation::E57_UINT32)
        .value("E57_INT64", MemoryRepresentation::E57_INT64)
        .value("E57_BOOL", MemoryRepresentation::E57_BOOL)
        .value("E57_REAL32", MemoryRepresentation::E57_REAL32)
        .value("E57_REAL64", MemoryRepresentation::E57_REAL64)
        .value("E57_USTRING", MemoryRepresentation::E57_USTRING)
        .export_values();
    py::enum_<ErrorCode>(m, "ErrorCode")
        .value("E57_SUCCESS", ErrorCode::E57_SUCCESS)
        .value("E57_ERROR_BAD_CV_HEADER", ErrorCode::E57_ERROR_BAD_CV_HEADER)
        .value("E57_ERROR_BAD_CV_PACKET", ErrorCode::E57_ERROR_BAD_CV_PACKET)
        .value("E57_ERROR_CHILD_INDEX_OUT_OF_BOUNDS", ErrorCode::E57_ERROR_CHILD_INDEX_OUT_OF_BOUNDS)
        .value("E57_ERROR_SET_TWICE", ErrorCode::E57_ERROR_SET_TWICE)
        .value("E57_ERROR_HOMOGENEOUS_VIOLATION", ErrorCode::E57_ERROR_HOMOGENEOUS_VIOLATION)
        .value("E57_ERROR_VALUE_NOT_REPRESENTABLE", ErrorCode::E57_ERROR_VALUE_NOT_REPRESENTABLE)
        .value("E57_ERROR_SCALED_VALUE_NOT_REPRESENTABLE", ErrorCode::E57_ERROR_SCALED_VALUE_NOT_REPRESENTABLE)
        .value("E57_ERROR_REAL64_TOO_LARGE", ErrorCode::E57_ERROR_REAL64_TOO_LARGE)
        .value("E57_ERROR_EXPECTING_NUMERIC", ErrorCode::E57_ERROR_EXPECTING_NUMERIC)
        .value("E57_ERROR_EXPECTING_USTRING", ErrorCode::E57_ERROR_EXPECTING_USTRING)
        .value("E57_ERROR_INTERNAL", ErrorCode::E57_ERROR_INTERNAL)
        .value("E57_ERROR_BAD_XML_FORMAT", ErrorCode::E57_ERROR_BAD_XML_FORMAT)
        .value("E57_ERROR_XML_PARSER", ErrorCode::E57_ERROR_XML_PARSER)
        .value("E57_ERROR_BAD_API_ARGUMENT", ErrorCode::E57_ERROR_BAD_API_ARGUMENT)
        .value("E57_ERROR_FILE_IS_READ_ONLY", ErrorCode::E57_ERROR_FILE_IS_READ_ONLY)
        .value("E57_ERROR_BAD_CHECKSUM", ErrorCode::E57_ERROR_BAD_CHECKSUM)
        .value("E57_ERROR_OPEN_FAILED", ErrorCode::E57_ERROR_OPEN_FAILED)
        .value("E57_ERROR_CLOSE_FAILED", ErrorCode::E57_ERROR_CLOSE_FAILED)
        .value("E57_ERROR_READ_FAILED", ErrorCode::E57_ERROR_READ_FAILED)
        .value("E57_ERROR_WRITE_FAILED", ErrorCode::E57_ERROR_WRITE_FAILED)
        .value("E57_ERROR_LSEEK_FAILED", ErrorCode::E57_ERROR_LSEEK_FAILED)
        .value("E57_ERROR_PATH_UNDEFINED", ErrorCode::E57_ERROR_PATH_UNDEFINED)
        .value("E57_ERROR_BAD_BUFFER", ErrorCode::E57_ERROR_BAD_BUFFER)
        .value("E57_ERROR_NO_BUFFER_FOR_ELEMENT", ErrorCode::E57_ERROR_NO_BUFFER_FOR_ELEMENT)
        .value("E57_ERROR_BUFFER_SIZE_MISMATCH", ErrorCode::E57_ERROR_BUFFER_SIZE_MISMATCH)
        .value("E57_ERROR_BUFFER_DUPLICATE_PATHNAME", ErrorCode::E57_ERROR_BUFFER_DUPLICATE_PATHNAME)
        .value("E57_ERROR_BAD_FILE_SIGNATURE", ErrorCode::E57_ERROR_BAD_FILE_SIGNATURE)
        .value("E57_ERROR_UNKNOWN_FILE_VERSION", ErrorCode::E57_ERROR_UNKNOWN_FILE_VERSION)
        .value("E57_ERROR_BAD_FILE_LENGTH", ErrorCode::E57_ERROR_BAD_FILE_LENGTH)
        .value("E57_ERROR_XML_PARSER_INIT", ErrorCode::E57_ERROR_XML_PARSER_INIT)
        .value("E57_ERROR_DUPLICATE_NAMESPACE_PREFIX", ErrorCode::E57_ERROR_DUPLICATE_NAMESPACE_PREFIX)
        .value("E57_ERROR_DUPLICATE_NAMESPACE_URI", ErrorCode::E57_ERROR_DUPLICATE_NAMESPACE_URI)
        .value("E57_ERROR_BAD_PROTOTYPE", ErrorCode::E57_ERROR_BAD_PROTOTYPE)
        .value("E57_ERROR_BAD_CODECS", ErrorCode::E57_ERROR_BAD_CODECS)
        .value("E57_ERROR_VALUE_OUT_OF_BOUNDS", ErrorCode::E57_ERROR_VALUE_OUT_OF_BOUNDS)
        .value("E57_ERROR_CONVERSION_REQUIRED", ErrorCode::E57_ERROR_CONVERSION_REQUIRED)
        .value("E57_ERROR_BAD_PATH_NAME", ErrorCode::E57_ERROR_BAD_PATH_NAME)
        .value("E57_ERROR_NOT_IMPLEMENTED", ErrorCode::E57_ERROR_NOT_IMPLEMENTED)
        .value("E57_ERROR_BAD_NODE_DOWNCAST", ErrorCode::E57_ERROR_BAD_NODE_DOWNCAST)
        .value("E57_ERROR_WRITER_NOT_OPEN", ErrorCode::E57_ERROR_WRITER_NOT_OPEN)
        .value("E57_ERROR_READER_NOT_OPEN", ErrorCode::E57_ERROR_READER_NOT_OPEN)
        .value("E57_ERROR_NODE_UNATTACHED", ErrorCode::E57_ERROR_NODE_UNATTACHED)
        .value("E57_ERROR_ALREADY_HAS_PARENT", ErrorCode::E57_ERROR_ALREADY_HAS_PARENT)
        .value("E57_ERROR_DIFFERENT_DEST_IMAGEFILE", ErrorCode::E57_ERROR_DIFFERENT_DEST_IMAGEFILE)
        .value("E57_ERROR_IMAGEFILE_NOT_OPEN", ErrorCode::E57_ERROR_IMAGEFILE_NOT_OPEN)
        .value("E57_ERROR_BUFFERS_NOT_COMPATIBLE", ErrorCode::E57_ERROR_BUFFERS_NOT_COMPATIBLE)
        .value("E57_ERROR_TOO_MANY_WRITERS", ErrorCode::E57_ERROR_TOO_MANY_WRITERS)
        .value("E57_ERROR_TOO_MANY_READERS", ErrorCode::E57_ERROR_TOO_MANY_READERS)
        .value("E57_ERROR_BAD_CONFIGURATION", ErrorCode::E57_ERROR_BAD_CONFIGURATION)
        .value("E57_ERROR_INVARIANCE_VIOLATION", ErrorCode::E57_ERROR_INVARIANCE_VIOLATION)
        .export_values();
    py::class_<Node> cls_Node(m, "Node");
    cls_Node.def("type", &Node::type);
    cls_Node.def("isRoot", &Node::isRoot);
    cls_Node.def("parent", &Node::parent);
    cls_Node.def("pathName", &Node::pathName);
    cls_Node.def("elementName", &Node::elementName);
    cls_Node.def("destImageFile", &Node::destImageFile);
    cls_Node.def("isAttached", &Node::isAttached);
    cls_Node.def("checkInvariant", &Node::checkInvariant, "doRecurse"_a=true, "doDowncast"_a=true);
    cls_Node.def("__repr__", [](const Node &node) {
        return "<Node '" + node.elementName() + "'>";
    });

    py::class_<StructureNode> cls_StructureNode(m, "StructureNode");
    cls_StructureNode.def(py::init<e57::ImageFile>(), "destImageFile"_a);
    cls_StructureNode.def("childCount", &StructureNode::childCount);
    cls_StructureNode.def("isDefined", &StructureNode::isDefined, "pathName"_a);
    cls_StructureNode.def("get", (Node (StructureNode::*)(int64_t) const) &StructureNode::get, "index"_a);
    cls_StructureNode.def("get", (Node (StructureNode::*)(const std::string &) const) &StructureNode::get, "pathName"_a);
    // Maybe there is a more elegant way to do this
    cls_StructureNode.def("set", [](StructureNode &node, const std::string &pathName, StructureNode &n){
        node.set(pathName, n);
    }, "pathName"_a, "n"_a);
    cls_StructureNode.def("set", [](StructureNode &node, const std::string &pathName, VectorNode &n){
        node.set(pathName, n);
    }, "pathName"_a, "n"_a);
    cls_StructureNode.def("set", [](StructureNode &node, const std::string &pathName, CompressedVectorNode &n){
        node.set(pathName, n);
    }, "pathName"_a, "n"_a);
    cls_StructureNode.def("set", [](StructureNode &node, const std::string &pathName, IntegerNode &n){
        node.set(pathName, n);
    }, "pathName"_a, "n"_a);
    cls_StructureNode.def("set", [](StructureNode &node, const std::string &pathName, ScaledIntegerNode &n){
        node.set(pathName, n);
    }, "pathName"_a, "n"_a);
    cls_StructureNode.def("set", [](StructureNode &node, const std::string &pathName, FloatNode &n){
        node.set(pathName, n);
    }, "pathName"_a, "n"_a);
    cls_StructureNode.def("set", [](StructureNode &node, const std::string &pathName, StringNode &n){
        node.set(pathName, n);
    }, "pathName"_a, "n"_a);
    cls_StructureNode.def(py::init<const e57::Node &>(), "n"_a);
    cls_StructureNode.def("isRoot", &StructureNode::isRoot);
    cls_StructureNode.def("parent", &StructureNode::parent);
    cls_StructureNode.def("pathName", &StructureNode::pathName);
    cls_StructureNode.def("elementName", &StructureNode::elementName);
    cls_StructureNode.def("destImageFile", &StructureNode::destImageFile);
    cls_StructureNode.def("isAttached", &StructureNode::isAttached);
    cls_StructureNode.def("checkInvariant", &StructureNode::checkInvariant, "doRecurse"_a=true, "doUpcast"_a=true);
    cls_StructureNode.def("__len__", &StructureNode::childCount);
    cls_StructureNode.def("__getitem__", [](const StructureNode &node, const std::string &pathName) {
        Node n = node.get(pathName);
        return cast_node(n);
    });
    cls_StructureNode.def("__getitem__", [](const StructureNode &node, int64_t index) {
        if (index >= node.childCount() || index < 0)
            throw py::index_error();
        Node n = node.get(index);
        return cast_node(n);
    });
    cls_StructureNode.def("__repr__", [](const StructureNode &node) {
        return "<StructureNode '" + node.elementName() + "'>";
    });

    py::class_<VectorNode> cls_VectorNode(m, "VectorNode");
    cls_VectorNode.def(py::init<e57::ImageFile, bool>(), "destImageFile"_a, "allowHeteroChildren"_a=false);
    cls_VectorNode.def("allowHeteroChildren", &VectorNode::allowHeteroChildren);
    cls_VectorNode.def("childCount", &VectorNode::childCount);
    cls_VectorNode.def("isDefined", &VectorNode::isDefined, "pathName"_a);
    cls_VectorNode.def("get", (Node (VectorNode::*)(int64_t) const) &VectorNode::get, "index"_a);
    cls_VectorNode.def("get", (Node (VectorNode::*)(const std::string &) const) &VectorNode::get, "pathName"_a);
    // Maybe there is a more elegant way to do this
    cls_VectorNode.def("append", [](VectorNode &v, StructureNode &node) { v.append(node); });
    cls_VectorNode.def("append", [](VectorNode &v, VectorNode &node) { v.append(node); });
    cls_VectorNode.def("append", [](VectorNode &v, CompressedVectorNode &node) { v.append(node); });
    cls_VectorNode.def("append", [](VectorNode &v, IntegerNode &node) { v.append(node); });
    cls_VectorNode.def("append", [](VectorNode &v, ScaledIntegerNode &node) { v.append(node); });
    cls_VectorNode.def("append", [](VectorNode &v, FloatNode &node) { v.append(node); });
    cls_VectorNode.def("append", [](VectorNode &v, StringNode &node) { v.append(node); });
    cls_VectorNode.def(py::init<const e57::Node &>(), "n"_a);
    cls_VectorNode.def("isRoot", &VectorNode::isRoot);
    cls_VectorNode.def("parent", &VectorNode::parent);
    cls_VectorNode.def("pathName", &VectorNode::pathName);
    cls_VectorNode.def("elementName", &VectorNode::elementName);
    cls_VectorNode.def("destImageFile", &VectorNode::destImageFile);
    cls_VectorNode.def("isAttached", &VectorNode::isAttached);
    cls_VectorNode.def("checkInvariant", &VectorNode::checkInvariant, "doRecurse"_a=true, "doUpcast"_a=true);
    cls_VectorNode.def("__len__", &VectorNode::childCount);
    cls_VectorNode.def("__getitem__", [](const VectorNode &node, const std::string &pathName) {
        Node n = node.get(pathName);
        return cast_node(n);
    });
    cls_VectorNode.def("__getitem__", [](const VectorNode &node, int64_t index) {
        if (index >= node.childCount() || index < 0)
            throw py::index_error();
        Node n = node.get(index);
        return cast_node(n);
    });
    cls_VectorNode.def("__repr__", [](const VectorNode &node) {
        return "<VectorNode '" + node.elementName() + "'>";
    });

    py::class_<SourceDestBuffer> cls_SourceDestBuffer(m, "SourceDestBuffer");
    cls_SourceDestBuffer.def("__init__", [](SourceDestBuffer &s,
                                            e57::ImageFile imf,
                                            const std::string pathName,
                                            py::buffer np_array,
                                            const size_t capacity,
                                            bool doConversion,
                                            bool doScaling,
                                            size_t stride=0) {
        py::buffer_info info = np_array.request();

        if (info.ndim != 1)
            throw std::runtime_error("Incompatible buffer dimension!");

        if (info.format == "b")
            new (&s) SourceDestBuffer(imf, pathName, static_cast<int8_t *>(info.ptr), capacity, doConversion, doScaling, (stride == 0) ? sizeof(int8_t) : stride);
        else if (info.format == "B")
            new (&s) SourceDestBuffer(imf, pathName, static_cast<uint8_t *>(info.ptr), capacity, doConversion, doScaling, (stride == 0) ? sizeof(uint8_t) : stride);
        else if (info.format == "h")
            new (&s) SourceDestBuffer(imf, pathName, static_cast<int16_t *>(info.ptr), capacity, doConversion, doScaling, (stride == 0) ? sizeof(int16_t) : stride);
        else if (info.format == "H")
            new (&s) SourceDestBuffer(imf, pathName, static_cast<uint16_t *>(info.ptr), capacity, doConversion, doScaling, (stride == 0) ? sizeof(uint16_t) : stride);
        else if (info.format == "l")
            new (&s) SourceDestBuffer(imf, pathName, static_cast<int32_t *>(info.ptr), capacity, doConversion, doScaling, (stride == 0) ? sizeof(int32_t) : stride);
        else if (info.format == "L")
            new (&s) SourceDestBuffer(imf, pathName, static_cast<uint32_t *>(info.ptr), capacity, doConversion, doScaling, (stride == 0) ? sizeof(uint32_t) : stride);
        else if (info.format == "q")
            new (&s) SourceDestBuffer(imf, pathName, static_cast<int64_t *>(info.ptr), capacity, doConversion, doScaling, (stride == 0) ? sizeof(int64_t) : stride);
        else if (info.format == "?")
            new (&s) SourceDestBuffer(imf, pathName, static_cast<bool *>(info.ptr), capacity, doConversion, doScaling, (stride == 0) ? sizeof(bool) : stride);
        else if (info.format == "f")
            new (&s) SourceDestBuffer(imf, pathName, static_cast<float *>(info.ptr), capacity, doConversion, doScaling, (stride == 0) ? sizeof(float) : stride);
        else if (info.format == "d")
            new (&s) SourceDestBuffer(imf, pathName, static_cast<double *>(info.ptr), capacity, doConversion, doScaling, (stride == 0) ? sizeof(double) : stride);
        else
            throw py::value_error("Incompatible type (integers: bBhHlLq, bool: ?, floats: fd)");
    },
    "destImageFile"_a, "pathName"_a, "b"_a, "capacity"_a, "doConversion"_a=false, "doScaling"_a=false, "stride"_a=0);
//    cls_SourceDestBuffer.def(py::init<e57::ImageFile, const std::string, int8_t *, const size_t, bool, bool, size_t>(), "destImageFile"_a, "pathName"_a, "b"_a, "capacity"_a, "doConversion"_a=false, "doScaling"_a=false, "stride"_a=sizeof(int8_t));
//    cls_SourceDestBuffer.def(py::init<e57::ImageFile, const std::string, uint8_t *, const size_t, bool, bool, size_t>(), "destImageFile"_a, "pathName"_a, "b"_a, "capacity"_a, "doConversion"_a=false, "doScaling"_a=false, "stride"_a=sizeof(uint8_t));
//    cls_SourceDestBuffer.def(py::init<e57::ImageFile, const std::string, int16_t *, const size_t, bool, bool, size_t>(), "destImageFile"_a, "pathName"_a, "b"_a, "capacity"_a, "doConversion"_a=false, "doScaling"_a=false, "stride"_a=sizeof(int16_t));
//    cls_SourceDestBuffer.def(py::init<e57::ImageFile, const std::string, uint16_t *, const size_t, bool, bool, size_t>(), "destImageFile"_a, "pathName"_a, "b"_a, "capacity"_a, "doConversion"_a=false, "doScaling"_a=false, "stride"_a=sizeof(uint16_t));
//    cls_SourceDestBuffer.def(py::init<e57::ImageFile, const std::string, int32_t *, const size_t, bool, bool, size_t>(), "destImageFile"_a, "pathName"_a, "b"_a, "capacity"_a, "doConversion"_a=false, "doScaling"_a=false, "stride"_a=sizeof(int32_t));
//    cls_SourceDestBuffer.def(py::init<e57::ImageFile, const std::string, uint32_t *, const size_t, bool, bool, size_t>(), "destImageFile"_a, "pathName"_a, "b"_a, "capacity"_a, "doConversion"_a=false, "doScaling"_a=false, "stride"_a=sizeof(uint32_t));
//    cls_SourceDestBuffer.def(py::init<e57::ImageFile, const std::string, int64_t *, const size_t, bool, bool, size_t>(), "destImageFile"_a, "pathName"_a, "b"_a, "capacity"_a, "doConversion"_a=false, "doScaling"_a=false, "stride"_a=sizeof(int64_t));
//    cls_SourceDestBuffer.def(py::init<e57::ImageFile, const std::string, bool *, const size_t, bool, bool, size_t>(), "destImageFile"_a, "pathName"_a, "b"_a, "capacity"_a, "doConversion"_a=false, "doScaling"_a=false, "stride"_a=sizeof(bool));
//    cls_SourceDestBuffer.def(py::init<e57::ImageFile, const std::string, float *, const size_t, bool, bool, size_t>(), "destImageFile"_a, "pathName"_a, "b"_a, "capacity"_a, "doConversion"_a=false, "doScaling"_a=false, "stride"_a=sizeof(float));
//    cls_SourceDestBuffer.def(py::init<e57::ImageFile, const std::string, double *, const size_t, bool, bool, size_t>(), "destImageFile"_a, "pathName"_a, "b"_a, "capacity"_a, "doConversion"_a=false, "doScaling"_a=false, "stride"_a=sizeof(double));
//    cls_SourceDestBuffer.def(py::init<e57::ImageFile, const std::string, std::vector<ustring> *>(), "destImageFile"_a, "pathName"_a, "b"_a);
    cls_SourceDestBuffer.def("pathName", &SourceDestBuffer::pathName);
    cls_SourceDestBuffer.def("capacity", &SourceDestBuffer::capacity);
    cls_SourceDestBuffer.def("doConversion", &SourceDestBuffer::doConversion);
    cls_SourceDestBuffer.def("doScaling", &SourceDestBuffer::doScaling);
    cls_SourceDestBuffer.def("stride", &SourceDestBuffer::stride);
    cls_SourceDestBuffer.def("checkInvariant", &SourceDestBuffer::checkInvariant, "doRecurse"_a=true);
    cls_SourceDestBuffer.def("__repr__", [](const SourceDestBuffer &bf) {
        return "<SourceDestBuffer '" + bf.pathName() + "'>";
    });

    py::class_<CompressedVectorReader> cls_CompressedVectorReader(m, "CompressedVectorReader");
    cls_CompressedVectorReader.def("read", (unsigned (CompressedVectorReader::*)(void)) &CompressedVectorReader::read);
    cls_CompressedVectorReader.def("read", (unsigned (CompressedVectorReader::*)(std::vector<SourceDestBuffer> &)) &CompressedVectorReader::read, "dbufs"_a);
    cls_CompressedVectorReader.def("seek", &CompressedVectorReader::seek, "recordNumber"_a);
    cls_CompressedVectorReader.def("close", &CompressedVectorReader::close);
    cls_CompressedVectorReader.def("isOpen", &CompressedVectorReader::isOpen);
    cls_CompressedVectorReader.def("compressedVectorNode", &CompressedVectorReader::compressedVectorNode);
    cls_CompressedVectorReader.def("checkInvariant", &CompressedVectorReader::checkInvariant, "doRecurse"_a=true);
    cls_CompressedVectorReader.def("__del__", [](CompressedVectorReader &r) { r.close(); });

    py::class_<CompressedVectorWriter> cls_CompressedVectorWriter(m, "CompressedVectorWriter");
    cls_CompressedVectorWriter.def("write", (void (CompressedVectorWriter::*)(const size_t)) &CompressedVectorWriter::write, "requestedRecordCount"_a);
    cls_CompressedVectorWriter.def("write", (void (CompressedVectorWriter::*)(std::vector<SourceDestBuffer> &, const size_t)) &CompressedVectorWriter::write, "sbufs"_a, "requestedRecordCount"_a);
    cls_CompressedVectorWriter.def("close", &CompressedVectorWriter::close);
    cls_CompressedVectorWriter.def("isOpen", &CompressedVectorWriter::isOpen);
    cls_CompressedVectorWriter.def("compressedVectorNode", &CompressedVectorWriter::compressedVectorNode);
    cls_CompressedVectorWriter.def("checkInvariant", &CompressedVectorWriter::checkInvariant, "doRecurse"_a=true);
    cls_CompressedVectorWriter.def("__del__", [](CompressedVectorWriter &r) { r.close(); });

    py::class_<CompressedVectorNode> cls_CompressedVectorNode(m, "CompressedVectorNode");
    cls_CompressedVectorNode.def(py::init<e57::ImageFile, e57::Node, e57::VectorNode>(), "destImageFile"_a, "prototype"_a, "codecs"_a);
    cls_CompressedVectorNode.def("__init__", [](CompressedVectorNode &n, e57::ImageFile &imf, e57::StructureNode &node, e57::VectorNode &vector_node) {
        new (&n) CompressedVectorNode(imf, node, vector_node);
    });
    cls_CompressedVectorNode.def("childCount", &CompressedVectorNode::childCount);
    cls_CompressedVectorNode.def("prototype", &CompressedVectorNode::prototype);
    cls_CompressedVectorNode.def("codecs", &CompressedVectorNode::codecs);
    cls_CompressedVectorNode.def("writer", &CompressedVectorNode::writer, "sbufs"_a);
    cls_CompressedVectorNode.def("reader", &CompressedVectorNode::reader, "dbufs"_a);
    cls_CompressedVectorNode.def(py::init<const e57::Node &>(), "n"_a);
    cls_CompressedVectorNode.def("isRoot", &CompressedVectorNode::isRoot);
    cls_CompressedVectorNode.def("parent", &CompressedVectorNode::parent);
    cls_CompressedVectorNode.def("pathName", &CompressedVectorNode::pathName);
    cls_CompressedVectorNode.def("elementName", &CompressedVectorNode::elementName);
    cls_CompressedVectorNode.def("destImageFile", &CompressedVectorNode::destImageFile);
    cls_CompressedVectorNode.def("isAttached", &CompressedVectorNode::isAttached);
    cls_CompressedVectorNode.def("checkInvariant", &CompressedVectorNode::checkInvariant, "doRecurse"_a=true, "doUpcast"_a=true);
    cls_CompressedVectorNode.def("__repr__", [](const CompressedVectorNode &node) {
        return "<CompressedVectorNode '" + node.elementName() + "'>";
    });

    py::class_<IntegerNode> cls_IntegerNode(m, "IntegerNode");
    cls_IntegerNode.def(py::init<e57::ImageFile, int64_t, int64_t, int64_t>(), "destImageFile"_a, "value"_a=0, "minimum"_a=INT64_MIN, "maximum"_a=INT64_MAX);
    cls_IntegerNode.def("value", &IntegerNode::value);
    cls_IntegerNode.def("minimum", &IntegerNode::minimum);
    cls_IntegerNode.def("maximum", &IntegerNode::maximum);
    cls_IntegerNode.def(py::init<const e57::Node &>(), "n"_a);
    cls_IntegerNode.def("isRoot", &IntegerNode::isRoot);
    cls_IntegerNode.def("parent", &IntegerNode::parent);
    cls_IntegerNode.def("pathName", &IntegerNode::pathName);
    cls_IntegerNode.def("elementName", &IntegerNode::elementName);
    cls_IntegerNode.def("destImageFile", &IntegerNode::destImageFile);
    cls_IntegerNode.def("isAttached", &IntegerNode::isAttached);
    cls_IntegerNode.def("checkInvariant", &IntegerNode::checkInvariant, "doRecurse"_a=true, "doUpcast"_a=true);
    cls_IntegerNode.def("__repr__", [](const IntegerNode &node) {
        return "<IntegerNode '" + node.elementName() + "'>";
    });

    py::class_<ScaledIntegerNode> cls_ScaledIntegerNode(m, "ScaledIntegerNode");
    cls_ScaledIntegerNode.def(py::init<e57::ImageFile, int64_t, int64_t, int64_t, double, double>(), "destImageFile"_a, "value"_a, "minimum"_a, "maximum"_a, "scale"_a=1.0, "offset"_a=0.0);
    cls_ScaledIntegerNode.def(py::init<e57::ImageFile, int, int64_t, int64_t, double, double>(), "destImageFile"_a, "value"_a, "minimum"_a, "maximum"_a, "scale"_a=1.0, "offset"_a=0.0);
    cls_ScaledIntegerNode.def(py::init<e57::ImageFile, int, int, int, double, double>(), "destImageFile"_a, "value"_a, "minimum"_a, "maximum"_a, "scale"_a=1.0, "offset"_a=0.0);
    cls_ScaledIntegerNode.def(py::init<e57::ImageFile, double, double, double, double, double>(), "destImageFile"_a, "scaledValue"_a, "scaledMinimum"_a, "scaledMaximum"_a, "scale"_a=1.0, "offset"_a=0.0);
    cls_ScaledIntegerNode.def("rawValue", &ScaledIntegerNode::rawValue);
    cls_ScaledIntegerNode.def("scaledValue", &ScaledIntegerNode::scaledValue);
    cls_ScaledIntegerNode.def("minimum", &ScaledIntegerNode::minimum);
    cls_ScaledIntegerNode.def("scaledMinimum", &ScaledIntegerNode::scaledMinimum);
    cls_ScaledIntegerNode.def("maximum", &ScaledIntegerNode::maximum);
    cls_ScaledIntegerNode.def("scaledMaximum", &ScaledIntegerNode::scaledMaximum);
    cls_ScaledIntegerNode.def("scale", &ScaledIntegerNode::scale);
    cls_ScaledIntegerNode.def("offset", &ScaledIntegerNode::offset);
    cls_ScaledIntegerNode.def(py::init<const e57::Node &>(), "n"_a);
    cls_ScaledIntegerNode.def("isRoot", &ScaledIntegerNode::isRoot);
    cls_ScaledIntegerNode.def("parent", &ScaledIntegerNode::parent);
    cls_ScaledIntegerNode.def("pathName", &ScaledIntegerNode::pathName);
    cls_ScaledIntegerNode.def("elementName", &ScaledIntegerNode::elementName);
    cls_ScaledIntegerNode.def("destImageFile", &ScaledIntegerNode::destImageFile);
    cls_ScaledIntegerNode.def("isAttached", &ScaledIntegerNode::isAttached);
    cls_ScaledIntegerNode.def("checkInvariant", &ScaledIntegerNode::checkInvariant, "doRecurse"_a=true, "doUpcast"_a=true);
    cls_ScaledIntegerNode.def("__repr__", [](const ScaledIntegerNode &node) {
        return "<ScaledIntegerNode '" + node.elementName() + "'>";
    });

    py::class_<FloatNode> cls_FloatNode(m, "FloatNode");
    cls_FloatNode.def(py::init<e57::ImageFile, double, FloatPrecision, double, double>(), "destImageFile"_a, "value"_a=0.0, "precision"_a=E57_DOUBLE, "minimum"_a=-DBL_MAX, "maximum"_a=DBL_MAX);
    cls_FloatNode.def("value", &FloatNode::value);
    cls_FloatNode.def("precision", &FloatNode::precision);
    cls_FloatNode.def("minimum", &FloatNode::minimum);
    cls_FloatNode.def("maximum", &FloatNode::maximum);
    cls_FloatNode.def(py::init<const e57::Node &>(), "n"_a);
    cls_FloatNode.def("isRoot", &FloatNode::isRoot);
    cls_FloatNode.def("parent", &FloatNode::parent);
    cls_FloatNode.def("pathName", &FloatNode::pathName);
    cls_FloatNode.def("elementName", &FloatNode::elementName);
    cls_FloatNode.def("destImageFile", &FloatNode::destImageFile);
    cls_FloatNode.def("isAttached", &FloatNode::isAttached);
    cls_FloatNode.def("checkInvariant", &FloatNode::checkInvariant, "doRecurse"_a=true, "doUpcast"_a=true);
    cls_FloatNode.def("__repr__", [](const FloatNode &node) {
        return "<FloatNode '" + node.elementName() + "'>";
    });

    py::class_<StringNode> cls_StringNode(m, "StringNode");
    cls_StringNode.def(py::init<e57::ImageFile, const std::string>(), "destImageFile"_a, "value"_a="");
    cls_StringNode.def("value", &StringNode::value);
    cls_StringNode.def(py::init<const e57::Node &>(), "n"_a);
    cls_StringNode.def("isRoot", &StringNode::isRoot);
    cls_StringNode.def("parent", &StringNode::parent);
    cls_StringNode.def("pathName", &StringNode::pathName);
    cls_StringNode.def("elementName", &StringNode::elementName);
    cls_StringNode.def("destImageFile", &StringNode::destImageFile);
    cls_StringNode.def("isAttached", &StringNode::isAttached);
    cls_StringNode.def("checkInvariant", &StringNode::checkInvariant, "doRecurse"_a=true, "doUpcast"_a=true);
    cls_StringNode.def("__repr__", [](const StringNode &node) {
        return "<StringNode '" + node.elementName() + "'>";
    });

    py::class_<BlobNode> cls_BlobNode(m, "BlobNode");
    cls_BlobNode.def(py::init<e57::ImageFile, int64_t>(), "destImageFile"_a, "byteCount"_a);
    cls_BlobNode.def("byteCount", &BlobNode::byteCount);
    cls_BlobNode.def("read", [](BlobNode& node, py::buffer buf, int64_t start, size_t count) {
        py::buffer_info info = buf.request();

        if (info.ndim != 1) {
            throw std::runtime_error("Incompatible buffer dimension!");
        }

        if (info.format != "B") {
            throw std::runtime_error("Incompatible buffer type!");
        }

        if (static_cast<size_t>(info.shape[0]) < count) {
            throw std::runtime_error("Buffer not large enough to read.");
        }

        node.read(reinterpret_cast<uint8_t*>(info.ptr), start, count);
    });
    cls_BlobNode.def("write", [](BlobNode& node, py::buffer buf, int64_t start, size_t count) {
        py::buffer_info info = buf.request();

        if (info.ndim != 1) {
            throw std::runtime_error("Incompatible buffer dimension!");
        }

        if (info.format != "B") {
            throw std::runtime_error("Incompatible buffer type!");
        }

        if (static_cast<size_t>(info.shape[0]) < count) {
            throw std::runtime_error("Buffer not large enough to write.");
        }

        node.write(reinterpret_cast<uint8_t*>(info.ptr), start, count);
    });
    cls_BlobNode.def(py::init<const e57::Node &>(), "n"_a);
    cls_BlobNode.def("isRoot", &BlobNode::isRoot);
    cls_BlobNode.def("parent", &BlobNode::parent);
    cls_BlobNode.def("pathName", &BlobNode::pathName);
    cls_BlobNode.def("elementName", &BlobNode::elementName);
    cls_BlobNode.def("destImageFile", &BlobNode::destImageFile);
    cls_BlobNode.def("isAttached", &BlobNode::isAttached);
    cls_BlobNode.def("checkInvariant", &BlobNode::checkInvariant, "doRecurse"_a=true, "doUpcast"_a=true);
    cls_BlobNode.def("__repr__", [](const BlobNode &node) {
        return "<BlobNode '" + node.elementName() + "'>";
    });
    cls_BlobNode.def("read_buffer", [](BlobNode &node) -> py::array {
        int64_t bufferSizeExpected = node.byteCount();
        py::array_t<uint8_t> arr(bufferSizeExpected);
        node.read(arr.mutable_data(), 0, bufferSizeExpected);
        return arr;
    });

    py::class_<ImageFile> (m, "ImageFile")
    .def(py::init<const std::string &, const std::string &, int>(), "fname"_a, "mode"_a, "checksumPolicy"_a=CHECKSUM_POLICY_ALL)
    .def("root", &ImageFile::root)
    .def("close", &ImageFile::close)
    .def("cancel", &ImageFile::cancel)
    .def("isOpen", &ImageFile::isOpen)
    .def("isWritable", &ImageFile::isWritable)
    .def("fileName", &ImageFile::fileName)
    .def("writerCount", &ImageFile::writerCount)
    .def("readerCount", &ImageFile::readerCount)
    .def("extensionsAdd", &ImageFile::extensionsAdd, "prefix"_a, "uri"_a)
// I couldn't wrap the overloaded function so I call it directly
    .def("extensionsLookupPrefix",  [](const ImageFile &im, std::string &prefix, std::string &uri) {
        return im.extensionsLookupPrefix(prefix, uri);
    }, "prefix"_a, "uri"_a)
    .def("extensionsLookupUri", &ImageFile::extensionsLookupUri, "uri"_a, "prefix"_a)
    .def("extensionsCount", &ImageFile::extensionsCount)
    .def("extensionsPrefix", &ImageFile::extensionsPrefix, "index"_a)
    .def("extensionsUri", &ImageFile::extensionsUri, "index"_a)
    .def("isElementNameExtended", &ImageFile::isElementNameExtended, "elementName"_a)
    .def("elementNameParse", &ImageFile::elementNameParse, "elementName"_a, "prefix"_a, "localPart"_a)
    .def("checkInvariant", &ImageFile::checkInvariant, "doRecurse"_a=true)
    .def("__repr__", [](const ImageFile &im) {
        return "<ImageFile '" + im.fileName() + "'>";
    });

//    py::class_<E57Exception> cls_E57Exception(m, "E57Exception");
//    cls_E57Exception.def("errorCode", &E57Exception::errorCode);
//    cls_E57Exception.def("context", &E57Exception::context);
//    cls_E57Exception.def("what", &E57Exception::what);
//    cls_E57Exception.def("sourceFileName", &E57Exception::sourceFileName);
//    cls_E57Exception.def("sourceFunctionName", &E57Exception::sourceFunctionName);
//    cls_E57Exception.def("sourceLineNumber", &E57Exception::sourceLineNumber);

//    py::class_<E57Utilities> cls_E57Utilities(m, "E57Utilities");
//    cls_E57Utilities.def(py::init<const std::string>(), "&"_a="");
//    cls_E57Utilities.def("getVersions", &E57Utilities::getVersions, "astmMajor"_a, "astmMinor"_a, "libraryId"_a);
//    cls_E57Utilities.def("errorCodeToString", &E57Utilities::errorCodeToString, "ecode"_a);

    py::bind_vector<std::vector<e57::SourceDestBuffer>>(m, "VectorSourceDestBuffer");
}
