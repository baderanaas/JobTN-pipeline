package deserializers;

import DTO.Hi_interns;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.apache.flink.api.common.serialization.DeserializationSchema;
import org.apache.flink.api.common.typeinfo.TypeInformation;

import java.io.IOException;

public class JSONValueDeserializationSchemaHiInterns implements DeserializationSchema<Hi_interns> {

    private final ObjectMapper objectMapper = new ObjectMapper();
    @Override
    public void open(InitializationContext context) throws Exception {
        DeserializationSchema.super.open(context);
    }

    @Override
    public Hi_interns deserialize(byte[] bytes) throws IOException {
        return objectMapper.readValue(bytes, Hi_interns.class);
    }

    @Override
    public boolean isEndOfStream(Hi_interns Hi_interns) {
        return false;
    }

    @Override
    public TypeInformation<Hi_interns> getProducedType() {
        return TypeInformation.of(Hi_interns.class);
    }
}
