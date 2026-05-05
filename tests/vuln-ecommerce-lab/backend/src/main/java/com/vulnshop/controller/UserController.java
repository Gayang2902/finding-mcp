package com.vulnshop.controller;

import com.vulnshop.dto.request.AdminUserUpdateRequest;
import com.vulnshop.dto.request.ChangePasswordRequest;
import com.vulnshop.dto.request.ProfileUpdateRequest;
import com.vulnshop.dto.response.UserResponse;
import com.vulnshop.entity.User;
import com.vulnshop.security.SecurityUtils;
import com.vulnshop.service.UserService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/users")
public class UserController {

    private final UserService userService;

    public UserController(UserService userService) {
        this.userService = userService;
    }

    @GetMapping("/profile")
    public ResponseEntity<UserResponse> getProfile() {
        Long currentUserId = SecurityUtils.getCurrentUserId();
        User user = userService.findById(currentUserId);
        return ResponseEntity.ok(userService.mapToResponse(user));
    }

    @PutMapping("/profile")
    public ResponseEntity<UserResponse> updateProfile(@RequestBody ProfileUpdateRequest request) {
        Long currentUserId = SecurityUtils.getCurrentUserId();
        return ResponseEntity.ok(userService.updateProfile(currentUserId, request));
    }

    @PutMapping("/password")
    public ResponseEntity<Void> changePassword(@RequestBody ChangePasswordRequest request) {
        Long currentUserId = SecurityUtils.getCurrentUserId();
        userService.changePassword(currentUserId, request);
        return ResponseEntity.ok().build();
    }

    // VULN: IDOR - any authenticated user can view any user's profile by ID
    @GetMapping("/{id}")
    public ResponseEntity<UserResponse> getUserById(@PathVariable Long id) {
        User user = userService.findById(id);
        return ResponseEntity.ok(userService.mapToResponse(user));
    }

    // VULN: Missing access control - should be admin only
    @GetMapping("/")
    public ResponseEntity<List<UserResponse>> getAllUsers() {
        return ResponseEntity.ok(userService.getAllUsers());
    }

    // VULN: MFAC - any authenticated user can change any user's role
    @PutMapping("/{id}/role")
    public ResponseEntity<UserResponse> updateUserRole(@PathVariable Long id, @RequestBody AdminUserUpdateRequest request) {
        return ResponseEntity.ok(userService.updateUserRole(id, request));
    }

    // VULN: Missing access control - should be admin only
    @DeleteMapping("/{id}")
    public ResponseEntity<Void> deleteUser(@PathVariable Long id) {
        userService.deleteUser(id);
        return ResponseEntity.noContent().build();
    }
}
