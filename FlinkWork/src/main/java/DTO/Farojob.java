package DTO;

import lombok.Data;

import java.sql.Timestamp;
import java.util.List;

@Data
public class Farojob {
    private String link;
    private String body;
    private Timestamp date;
}
