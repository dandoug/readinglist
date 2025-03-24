-- Table for roles
CREATE TABLE role (
    id INT AUTO_INCREMENT PRIMARY KEY,                    -- Primary Key for Role
    name VARCHAR(255) NOT NULL UNIQUE,                    -- Unique name for the role
    description VARCHAR(255),                             -- Description of the role
    permissions TEXT,                                     -- Permissions as a text field (JSON or other format)
    update_datetime DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP -- Timestamp when role was last updated
);

-- Table for users
CREATE TABLE user (
    id INT AUTO_INCREMENT PRIMARY KEY,                    -- Primary Key for User
    email VARCHAR(255) UNIQUE NOT NULL,                   -- User email, must be unique
    username VARCHAR(255) UNIQUE,                         -- Optional username for the user
    password VARCHAR(255),                                -- Password field (nullable)
    active BOOLEAN DEFAULT TRUE,                          -- Indicates if the user account is active
    fs_uniquifier VARCHAR(64) UNIQUE NOT NULL,            -- Unique identifier for user
    confirmed_at DATETIME,                                -- Confirmation timestamp
    last_login_at DATETIME,                               -- Timestamp of the last login
    current_login_at DATETIME,                            -- Timestamp for the current login
    last_login_ip VARCHAR(100),                           -- IP address of the user's last login
    current_login_ip VARCHAR(100),                        -- IP address of the current login
    login_count INT DEFAULT 0,                            -- Login attempt count
    tf_primary_method VARCHAR(64),                        -- 2FA primary method
    tf_totp_secret TEXT,                                  -- TOTP secret (nullable)
    tf_phone_number VARCHAR(128),                         -- Phone number for SMS-based 2FA
    us_phone_number VARCHAR(128) UNIQUE,                  -- Unified phone number (nullable, unique)
    us_totp_secrets TEXT,                                 -- Unified TOTP secrets (nullable)
    fs_webauthn_user_handle VARCHAR(64) UNIQUE,           -- Nullable unique WebAuthn user handle
    mf_recovery_codes TEXT,                               -- Recovery codes for multifactor auth
    create_datetime DATETIME DEFAULT CURRENT_TIMESTAMP,   -- Account creation timestamp
    update_datetime DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP -- Update timestamp
);

-- Many-to-Many relationship table for users and roles
CREATE TABLE roles_users (
    user_id INT NOT NULL,                                 -- User ID (foreign key)
    role_id INT NOT NULL,                                 -- Role ID (foreign key)
    PRIMARY KEY (user_id, role_id),                       -- Composite primary key
    FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE, -- Foreign key to user
    FOREIGN KEY (role_id) REFERENCES role(id) ON DELETE CASCADE  -- Foreign key to role
);

-- Table for WebAuthn
CREATE TABLE webauthn (
    id INT AUTO_INCREMENT PRIMARY KEY,                    -- Primary Key for WebAuthn
    credential_id BLOB NOT NULL,                          -- Credential ID (binary, index a portion)
    UNIQUE KEY (credential_id(255)),                      -- Table-level UNIQUE key with length
    public_key BLOB NOT NULL,                             -- Public key associated with the credential
    sign_count INT DEFAULT 0,                             -- Signature counter
    transports TEXT,                                      -- Transport type(s)
    backup_state BOOLEAN NOT NULL,                        -- Indicates if the credential is a backup
    device_type VARCHAR(64) NOT NULL,                     -- Type of WebAuthn device
    extensions VARCHAR(255),                              -- Extensions (optional, JSON or other format)
    create_datetime DATETIME DEFAULT CURRENT_TIMESTAMP,   -- Creation timestamp for the credential
    lastuse_datetime DATETIME NOT NULL,                   -- Last use timestamp
    name VARCHAR(64) NOT NULL,                            -- Name of the credential (must be unique per user)
    `usage` VARCHAR(64) NOT NULL,                           -- Usage type (e.g., "first factor", "second factor")
    user_id INT NOT NULL,                                 -- Foreign key to User
    FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE  -- Foreign key with cascade
);
