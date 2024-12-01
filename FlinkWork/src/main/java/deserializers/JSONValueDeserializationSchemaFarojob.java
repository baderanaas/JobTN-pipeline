package deserializers;

import DTO.Farojob;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.apache.flink.api.common.serialization.DeserializationSchema;
import org.apache.flink.api.common.typeinfo.TypeInformation;

import java.io.IOException;

public class JSONValueDeserializationSchemaFarojob implements DeserializationSchema<Farojob> {

    private final ObjectMapper objectMapper = new ObjectMapper();
    @Override
    public void open(InitializationContext context) throws Exception {
        DeserializationSchema.super.open(context);
    }

    @Override
    public Farojob deserialize(byte[] bytes) throws IOException {
        return objectMapper.readValue(bytes, Farojob.class);
    }

    @Override
    public boolean isEndOfStream(Farojob Farojob) {
        return false;
    }

    @Override
    public TypeInformation<Farojob> getProducedType() {
        return TypeInformation.of(Farojob.class);
    }
}