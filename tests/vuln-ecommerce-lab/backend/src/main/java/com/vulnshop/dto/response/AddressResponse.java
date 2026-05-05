package com.vulnshop.dto.response;

import com.vulnshop.entity.AddressLabel;
import lombok.*;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class AddressResponse {

    private Long id;
    private AddressLabel label;
    private String fullName;
    private String streetAddress;
    private String streetAddress2;
    private String city;
    private String state;
    private String zipCode;
    private String country;
    private String phone;
    private boolean isDefault;
}
