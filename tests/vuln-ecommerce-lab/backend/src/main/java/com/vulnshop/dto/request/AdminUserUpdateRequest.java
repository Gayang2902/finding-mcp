package com.vulnshop.dto.request;

import com.vulnshop.entity.Role;
import lombok.*;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class AdminUserUpdateRequest {

    private Role role;

    private Boolean enabled;
}
