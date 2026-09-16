# Call-path stack analysis

- Functions in callgraph: 651
- Functions with known static stack: 606
- Callgraph edges considered: 2756
- Callgraph nodes without a known stack value: 45
- Unknown stack functions: 0
- Maximum path length considered: 651 functions

## Highest known call paths

Values are sums of Keil function stack values. Nodes without a known static stack value remain on the call path and contribute 0 B, including missing, ambiguous, and unknown values. This default does not prove that their actual stack usage is zero. Paths stop at recursive cycles.

### 1. 2832 B (19 frames)

1. `cell_task (16 B) — cellular/src/cell_task.c`
2. `process_message (8 B) — cellular/src/cell_task.c`
3. `connection_process (16 B) — cellular/src/cell_connect.c`
4. `perform_action (456 B) — cellular/src/cell_connect.c`
5. `start_registration (24 B) — cellular/src/cell_connect.c`
6. `check_operator_status (152 B) — cellular/src/cell_connect.c`
7. `execute_command (32 B) — cellular/src/cell_connect.c`
8. `config_pdp_wrapper (16 B) — cellular/src/cell_connect.c`
9. `semtech_pdp_settings_set (16 B) — modem/src/cell_modem_semtech.c`
10. `define_pdp_context (232 B) — modem/src/cell_modem_semtech.c`
11. `at_command_request (176 B) — modem/src/cell_at.c`
12. `process_remaining_data (136 B) — modem/src/cell_at.c`
13. `urc_parse_unsolicited_response (16 B) — modem/src/cell_urc.c`
14. `parse_urc_crtdcp (1384 B) — modem/src/cell_urc.c`
15. `quectel_handle_urc_socket_incoming (16 B) — modem/src/cell_modem_quectel.c`
16. `socket_process_urc_incoming_connection (16 B) — cellular/src/cell_socket.c`
17. `socket_close_wrapper (16 B) — cellular/src/cell_socket.c`
18. `semtech_socket_close (24 B) — modem/src/cell_modem_semtech.c`
19. `get_tcp_socket_status (80 B) — modem/src/cell_modem_semtech.c`

### 2. 2832 B (19 frames)

1. `cell_task (16 B) — cellular/src/cell_task.c`
2. `process_message (8 B) — cellular/src/cell_task.c`
3. `connection_process (16 B) — cellular/src/cell_connect.c`
4. `perform_action (456 B) — cellular/src/cell_connect.c`
5. `start_registration (24 B) — cellular/src/cell_connect.c`
6. `check_operator_status (152 B) — cellular/src/cell_connect.c`
7. `execute_command (32 B) — cellular/src/cell_connect.c`
8. `config_pdp_wrapper (16 B) — cellular/src/cell_connect.c`
9. `semtech_pdp_settings_set (16 B) — modem/src/cell_modem_semtech.c`
10. `define_pdp_context (232 B) — modem/src/cell_modem_semtech.c`
11. `at_command_request (176 B) — modem/src/cell_at.c`
12. `process_remaining_data (136 B) — modem/src/cell_at.c`
13. `urc_parse_unsolicited_response (16 B) — modem/src/cell_urc.c`
14. `parse_urc_crtdcp (1384 B) — modem/src/cell_urc.c`
15. `semtech_handle_urc_ktcp_srvreq (16 B) — modem/src/cell_modem_semtech.c`
16. `socket_process_urc_incoming_connection (16 B) — cellular/src/cell_socket.c`
17. `socket_close_wrapper (16 B) — cellular/src/cell_socket.c`
18. `semtech_socket_close (24 B) — modem/src/cell_modem_semtech.c`
19. `get_tcp_socket_status (80 B) — modem/src/cell_modem_semtech.c`

### 3. 2832 B (19 frames)

1. `cell_task (16 B) — cellular/src/cell_task.c`
2. `process_message (8 B) — cellular/src/cell_task.c`
3. `connection_process (16 B) — cellular/src/cell_connect.c`
4. `perform_action (456 B) — cellular/src/cell_connect.c`
5. `start_registration (24 B) — cellular/src/cell_connect.c`
6. `check_operator_status (152 B) — cellular/src/cell_connect.c`
7. `execute_command (32 B) — cellular/src/cell_connect.c`
8. `config_pdp_wrapper (16 B) — cellular/src/cell_connect.c`
9. `semtech_pdp_settings_set (16 B) — modem/src/cell_modem_semtech.c`
10. `semtech_pdp_authentication_set (232 B) — modem/src/cell_modem_semtech.c`
11. `at_command_request (176 B) — modem/src/cell_at.c`
12. `process_remaining_data (136 B) — modem/src/cell_at.c`
13. `urc_parse_unsolicited_response (16 B) — modem/src/cell_urc.c`
14. `parse_urc_crtdcp (1384 B) — modem/src/cell_urc.c`
15. `quectel_handle_urc_socket_incoming (16 B) — modem/src/cell_modem_quectel.c`
16. `socket_process_urc_incoming_connection (16 B) — cellular/src/cell_socket.c`
17. `socket_close_wrapper (16 B) — cellular/src/cell_socket.c`
18. `semtech_socket_close (24 B) — modem/src/cell_modem_semtech.c`
19. `get_tcp_socket_status (80 B) — modem/src/cell_modem_semtech.c`

### 4. 2832 B (19 frames)

1. `cell_task (16 B) — cellular/src/cell_task.c`
2. `process_message (8 B) — cellular/src/cell_task.c`
3. `connection_process (16 B) — cellular/src/cell_connect.c`
4. `perform_action (456 B) — cellular/src/cell_connect.c`
5. `start_registration (24 B) — cellular/src/cell_connect.c`
6. `check_operator_status (152 B) — cellular/src/cell_connect.c`
7. `execute_command (32 B) — cellular/src/cell_connect.c`
8. `config_pdp_wrapper (16 B) — cellular/src/cell_connect.c`
9. `semtech_pdp_settings_set (16 B) — modem/src/cell_modem_semtech.c`
10. `semtech_pdp_authentication_set (232 B) — modem/src/cell_modem_semtech.c`
11. `at_command_request (176 B) — modem/src/cell_at.c`
12. `process_remaining_data (136 B) — modem/src/cell_at.c`
13. `urc_parse_unsolicited_response (16 B) — modem/src/cell_urc.c`
14. `parse_urc_crtdcp (1384 B) — modem/src/cell_urc.c`
15. `semtech_handle_urc_ktcp_srvreq (16 B) — modem/src/cell_modem_semtech.c`
16. `socket_process_urc_incoming_connection (16 B) — cellular/src/cell_socket.c`
17. `socket_close_wrapper (16 B) — cellular/src/cell_socket.c`
18. `semtech_socket_close (24 B) — modem/src/cell_modem_semtech.c`
19. `get_tcp_socket_status (80 B) — modem/src/cell_modem_semtech.c`

### 5. 2824 B (18 frames)

1. `cell_task (16 B) — cellular/src/cell_task.c`
2. `process_message (8 B) — cellular/src/cell_task.c`
3. `connection_process (16 B) — cellular/src/cell_connect.c`
4. `perform_action (456 B) — cellular/src/cell_connect.c`
5. `start_registration (24 B) — cellular/src/cell_connect.c`
6. `check_operator_status (152 B) — cellular/src/cell_connect.c`
7. `execute_command (32 B) — cellular/src/cell_connect.c`
8. `config_pdp_wrapper (16 B) — cellular/src/cell_connect.c`
9. `quectel_pdp_settings_set (240 B) — modem/src/cell_modem_quectel.c`
10. `at_command_request (176 B) — modem/src/cell_at.c`
11. `process_remaining_data (136 B) — modem/src/cell_at.c`
12. `urc_parse_unsolicited_response (16 B) — modem/src/cell_urc.c`
13. `parse_urc_crtdcp (1384 B) — modem/src/cell_urc.c`
14. `quectel_handle_urc_socket_incoming (16 B) — modem/src/cell_modem_quectel.c`
15. `socket_process_urc_incoming_connection (16 B) — cellular/src/cell_socket.c`
16. `socket_close_wrapper (16 B) — cellular/src/cell_socket.c`
17. `semtech_socket_close (24 B) — modem/src/cell_modem_semtech.c`
18. `get_tcp_socket_status (80 B) — modem/src/cell_modem_semtech.c`

### 6. 2824 B (18 frames)

1. `cell_task (16 B) — cellular/src/cell_task.c`
2. `process_message (8 B) — cellular/src/cell_task.c`
3. `connection_process (16 B) — cellular/src/cell_connect.c`
4. `perform_action (456 B) — cellular/src/cell_connect.c`
5. `start_registration (24 B) — cellular/src/cell_connect.c`
6. `check_operator_status (152 B) — cellular/src/cell_connect.c`
7. `execute_command (32 B) — cellular/src/cell_connect.c`
8. `config_pdp_wrapper (16 B) — cellular/src/cell_connect.c`
9. `quectel_pdp_settings_set (240 B) — modem/src/cell_modem_quectel.c`
10. `at_command_request (176 B) — modem/src/cell_at.c`
11. `process_remaining_data (136 B) — modem/src/cell_at.c`
12. `urc_parse_unsolicited_response (16 B) — modem/src/cell_urc.c`
13. `parse_urc_crtdcp (1384 B) — modem/src/cell_urc.c`
14. `semtech_handle_urc_ktcp_srvreq (16 B) — modem/src/cell_modem_semtech.c`
15. `socket_process_urc_incoming_connection (16 B) — cellular/src/cell_socket.c`
16. `socket_close_wrapper (16 B) — cellular/src/cell_socket.c`
17. `semtech_socket_close (24 B) — modem/src/cell_modem_semtech.c`
18. `get_tcp_socket_status (80 B) — modem/src/cell_modem_semtech.c`

### 7. 2824 B (19 frames)

1. `cell_task (16 B) — cellular/src/cell_task.c`
2. `process_message (8 B) — cellular/src/cell_task.c`
3. `connection_process (16 B) — cellular/src/cell_connect.c`
4. `perform_action (456 B) — cellular/src/cell_connect.c`
5. `start_registration (24 B) — cellular/src/cell_connect.c`
6. `check_operator_status (152 B) — cellular/src/cell_connect.c`
7. `execute_command (32 B) — cellular/src/cell_connect.c`
8. `config_pdp_wrapper (16 B) — cellular/src/cell_connect.c`
9. `semtech_pdp_settings_set (16 B) — modem/src/cell_modem_semtech.c`
10. `define_pdp_context (232 B) — modem/src/cell_modem_semtech.c`
11. `at_command_request (176 B) — modem/src/cell_at.c`
12. `process_remaining_data (136 B) — modem/src/cell_at.c`
13. `urc_parse_unsolicited_response (16 B) — modem/src/cell_urc.c`
14. `parse_urc_crtdcp (1384 B) — modem/src/cell_urc.c`
15. `quectel_handle_urc_socket_incoming (16 B) — modem/src/cell_modem_quectel.c`
16. `socket_process_urc_incoming_connection (16 B) — cellular/src/cell_socket.c`
17. `socket_close_wrapper (16 B) — cellular/src/cell_socket.c`
18. `semtech_socket_close (24 B) — modem/src/cell_modem_semtech.c`
19. `tcp_close (72 B) — modem/src/cell_modem_semtech.c`

### 8. 2824 B (19 frames)

1. `cell_task (16 B) — cellular/src/cell_task.c`
2. `process_message (8 B) — cellular/src/cell_task.c`
3. `connection_process (16 B) — cellular/src/cell_connect.c`
4. `perform_action (456 B) — cellular/src/cell_connect.c`
5. `start_registration (24 B) — cellular/src/cell_connect.c`
6. `check_operator_status (152 B) — cellular/src/cell_connect.c`
7. `execute_command (32 B) — cellular/src/cell_connect.c`
8. `config_pdp_wrapper (16 B) — cellular/src/cell_connect.c`
9. `semtech_pdp_settings_set (16 B) — modem/src/cell_modem_semtech.c`
10. `define_pdp_context (232 B) — modem/src/cell_modem_semtech.c`
11. `at_command_request (176 B) — modem/src/cell_at.c`
12. `process_remaining_data (136 B) — modem/src/cell_at.c`
13. `urc_parse_unsolicited_response (16 B) — modem/src/cell_urc.c`
14. `parse_urc_crtdcp (1384 B) — modem/src/cell_urc.c`
15. `quectel_handle_urc_socket_incoming (16 B) — modem/src/cell_modem_quectel.c`
16. `socket_process_urc_incoming_connection (16 B) — cellular/src/cell_socket.c`
17. `socket_close_wrapper (16 B) — cellular/src/cell_socket.c`
18. `semtech_socket_close (24 B) — modem/src/cell_modem_semtech.c`
19. `tcp_delete (72 B) — modem/src/cell_modem_semtech.c`

### 9. 2824 B (19 frames)

1. `cell_task (16 B) — cellular/src/cell_task.c`
2. `process_message (8 B) — cellular/src/cell_task.c`
3. `connection_process (16 B) — cellular/src/cell_connect.c`
4. `perform_action (456 B) — cellular/src/cell_connect.c`
5. `start_registration (24 B) — cellular/src/cell_connect.c`
6. `check_operator_status (152 B) — cellular/src/cell_connect.c`
7. `execute_command (32 B) — cellular/src/cell_connect.c`
8. `config_pdp_wrapper (16 B) — cellular/src/cell_connect.c`
9. `semtech_pdp_settings_set (16 B) — modem/src/cell_modem_semtech.c`
10. `define_pdp_context (232 B) — modem/src/cell_modem_semtech.c`
11. `at_command_request (176 B) — modem/src/cell_at.c`
12. `process_remaining_data (136 B) — modem/src/cell_at.c`
13. `urc_parse_unsolicited_response (16 B) — modem/src/cell_urc.c`
14. `parse_urc_crtdcp (1384 B) — modem/src/cell_urc.c`
15. `semtech_handle_urc_ktcp_srvreq (16 B) — modem/src/cell_modem_semtech.c`
16. `socket_process_urc_incoming_connection (16 B) — cellular/src/cell_socket.c`
17. `socket_close_wrapper (16 B) — cellular/src/cell_socket.c`
18. `semtech_socket_close (24 B) — modem/src/cell_modem_semtech.c`
19. `tcp_close (72 B) — modem/src/cell_modem_semtech.c`

### 10. 2824 B (19 frames)

1. `cell_task (16 B) — cellular/src/cell_task.c`
2. `process_message (8 B) — cellular/src/cell_task.c`
3. `connection_process (16 B) — cellular/src/cell_connect.c`
4. `perform_action (456 B) — cellular/src/cell_connect.c`
5. `start_registration (24 B) — cellular/src/cell_connect.c`
6. `check_operator_status (152 B) — cellular/src/cell_connect.c`
7. `execute_command (32 B) — cellular/src/cell_connect.c`
8. `config_pdp_wrapper (16 B) — cellular/src/cell_connect.c`
9. `semtech_pdp_settings_set (16 B) — modem/src/cell_modem_semtech.c`
10. `define_pdp_context (232 B) — modem/src/cell_modem_semtech.c`
11. `at_command_request (176 B) — modem/src/cell_at.c`
12. `process_remaining_data (136 B) — modem/src/cell_at.c`
13. `urc_parse_unsolicited_response (16 B) — modem/src/cell_urc.c`
14. `parse_urc_crtdcp (1384 B) — modem/src/cell_urc.c`
15. `semtech_handle_urc_ktcp_srvreq (16 B) — modem/src/cell_modem_semtech.c`
16. `socket_process_urc_incoming_connection (16 B) — cellular/src/cell_socket.c`
17. `socket_close_wrapper (16 B) — cellular/src/cell_socket.c`
18. `semtech_socket_close (24 B) — modem/src/cell_modem_semtech.c`
19. `tcp_delete (72 B) — modem/src/cell_modem_semtech.c`

### 11. 2824 B (19 frames)

1. `cell_task (16 B) — cellular/src/cell_task.c`
2. `process_message (8 B) — cellular/src/cell_task.c`
3. `connection_process (16 B) — cellular/src/cell_connect.c`
4. `perform_action (456 B) — cellular/src/cell_connect.c`
5. `start_registration (24 B) — cellular/src/cell_connect.c`
6. `check_operator_status (152 B) — cellular/src/cell_connect.c`
7. `execute_command (32 B) — cellular/src/cell_connect.c`
8. `config_pdp_wrapper (16 B) — cellular/src/cell_connect.c`
9. `semtech_pdp_settings_set (16 B) — modem/src/cell_modem_semtech.c`
10. `semtech_pdp_authentication_set (232 B) — modem/src/cell_modem_semtech.c`
11. `at_command_request (176 B) — modem/src/cell_at.c`
12. `process_remaining_data (136 B) — modem/src/cell_at.c`
13. `urc_parse_unsolicited_response (16 B) — modem/src/cell_urc.c`
14. `parse_urc_crtdcp (1384 B) — modem/src/cell_urc.c`
15. `quectel_handle_urc_socket_incoming (16 B) — modem/src/cell_modem_quectel.c`
16. `socket_process_urc_incoming_connection (16 B) — cellular/src/cell_socket.c`
17. `socket_close_wrapper (16 B) — cellular/src/cell_socket.c`
18. `semtech_socket_close (24 B) — modem/src/cell_modem_semtech.c`
19. `tcp_close (72 B) — modem/src/cell_modem_semtech.c`

### 12. 2824 B (19 frames)

1. `cell_task (16 B) — cellular/src/cell_task.c`
2. `process_message (8 B) — cellular/src/cell_task.c`
3. `connection_process (16 B) — cellular/src/cell_connect.c`
4. `perform_action (456 B) — cellular/src/cell_connect.c`
5. `start_registration (24 B) — cellular/src/cell_connect.c`
6. `check_operator_status (152 B) — cellular/src/cell_connect.c`
7. `execute_command (32 B) — cellular/src/cell_connect.c`
8. `config_pdp_wrapper (16 B) — cellular/src/cell_connect.c`
9. `semtech_pdp_settings_set (16 B) — modem/src/cell_modem_semtech.c`
10. `semtech_pdp_authentication_set (232 B) — modem/src/cell_modem_semtech.c`
11. `at_command_request (176 B) — modem/src/cell_at.c`
12. `process_remaining_data (136 B) — modem/src/cell_at.c`
13. `urc_parse_unsolicited_response (16 B) — modem/src/cell_urc.c`
14. `parse_urc_crtdcp (1384 B) — modem/src/cell_urc.c`
15. `quectel_handle_urc_socket_incoming (16 B) — modem/src/cell_modem_quectel.c`
16. `socket_process_urc_incoming_connection (16 B) — cellular/src/cell_socket.c`
17. `socket_close_wrapper (16 B) — cellular/src/cell_socket.c`
18. `semtech_socket_close (24 B) — modem/src/cell_modem_semtech.c`
19. `tcp_delete (72 B) — modem/src/cell_modem_semtech.c`

### 13. 2824 B (19 frames)

1. `cell_task (16 B) — cellular/src/cell_task.c`
2. `process_message (8 B) — cellular/src/cell_task.c`
3. `connection_process (16 B) — cellular/src/cell_connect.c`
4. `perform_action (456 B) — cellular/src/cell_connect.c`
5. `start_registration (24 B) — cellular/src/cell_connect.c`
6. `check_operator_status (152 B) — cellular/src/cell_connect.c`
7. `execute_command (32 B) — cellular/src/cell_connect.c`
8. `config_pdp_wrapper (16 B) — cellular/src/cell_connect.c`
9. `semtech_pdp_settings_set (16 B) — modem/src/cell_modem_semtech.c`
10. `semtech_pdp_authentication_set (232 B) — modem/src/cell_modem_semtech.c`
11. `at_command_request (176 B) — modem/src/cell_at.c`
12. `process_remaining_data (136 B) — modem/src/cell_at.c`
13. `urc_parse_unsolicited_response (16 B) — modem/src/cell_urc.c`
14. `parse_urc_crtdcp (1384 B) — modem/src/cell_urc.c`
15. `semtech_handle_urc_ktcp_srvreq (16 B) — modem/src/cell_modem_semtech.c`
16. `socket_process_urc_incoming_connection (16 B) — cellular/src/cell_socket.c`
17. `socket_close_wrapper (16 B) — cellular/src/cell_socket.c`
18. `semtech_socket_close (24 B) — modem/src/cell_modem_semtech.c`
19. `tcp_close (72 B) — modem/src/cell_modem_semtech.c`

### 14. 2824 B (19 frames)

1. `cell_task (16 B) — cellular/src/cell_task.c`
2. `process_message (8 B) — cellular/src/cell_task.c`
3. `connection_process (16 B) — cellular/src/cell_connect.c`
4. `perform_action (456 B) — cellular/src/cell_connect.c`
5. `start_registration (24 B) — cellular/src/cell_connect.c`
6. `check_operator_status (152 B) — cellular/src/cell_connect.c`
7. `execute_command (32 B) — cellular/src/cell_connect.c`
8. `config_pdp_wrapper (16 B) — cellular/src/cell_connect.c`
9. `semtech_pdp_settings_set (16 B) — modem/src/cell_modem_semtech.c`
10. `semtech_pdp_authentication_set (232 B) — modem/src/cell_modem_semtech.c`
11. `at_command_request (176 B) — modem/src/cell_at.c`
12. `process_remaining_data (136 B) — modem/src/cell_at.c`
13. `urc_parse_unsolicited_response (16 B) — modem/src/cell_urc.c`
14. `parse_urc_crtdcp (1384 B) — modem/src/cell_urc.c`
15. `semtech_handle_urc_ktcp_srvreq (16 B) — modem/src/cell_modem_semtech.c`
16. `socket_process_urc_incoming_connection (16 B) — cellular/src/cell_socket.c`
17. `socket_close_wrapper (16 B) — cellular/src/cell_socket.c`
18. `semtech_socket_close (24 B) — modem/src/cell_modem_semtech.c`
19. `tcp_delete (72 B) — modem/src/cell_modem_semtech.c`

### 15. 2816 B (18 frames)

1. `cell_task (16 B) — cellular/src/cell_task.c`
2. `process_message (8 B) — cellular/src/cell_task.c`
3. `connection_process (16 B) — cellular/src/cell_connect.c`
4. `perform_action (456 B) — cellular/src/cell_connect.c`
5. `start_registration (24 B) — cellular/src/cell_connect.c`
6. `check_operator_status (152 B) — cellular/src/cell_connect.c`
7. `execute_command (32 B) — cellular/src/cell_connect.c`
8. `config_pdp_wrapper (16 B) — cellular/src/cell_connect.c`
9. `quectel_pdp_settings_set (240 B) — modem/src/cell_modem_quectel.c`
10. `at_command_request (176 B) — modem/src/cell_at.c`
11. `process_remaining_data (136 B) — modem/src/cell_at.c`
12. `urc_parse_unsolicited_response (16 B) — modem/src/cell_urc.c`
13. `parse_urc_crtdcp (1384 B) — modem/src/cell_urc.c`
14. `quectel_handle_urc_socket_incoming (16 B) — modem/src/cell_modem_quectel.c`
15. `socket_process_urc_incoming_connection (16 B) — cellular/src/cell_socket.c`
16. `socket_close_wrapper (16 B) — cellular/src/cell_socket.c`
17. `semtech_socket_close (24 B) — modem/src/cell_modem_semtech.c`
18. `tcp_close (72 B) — modem/src/cell_modem_semtech.c`

### 16. 2816 B (18 frames)

1. `cell_task (16 B) — cellular/src/cell_task.c`
2. `process_message (8 B) — cellular/src/cell_task.c`
3. `connection_process (16 B) — cellular/src/cell_connect.c`
4. `perform_action (456 B) — cellular/src/cell_connect.c`
5. `start_registration (24 B) — cellular/src/cell_connect.c`
6. `check_operator_status (152 B) — cellular/src/cell_connect.c`
7. `execute_command (32 B) — cellular/src/cell_connect.c`
8. `config_pdp_wrapper (16 B) — cellular/src/cell_connect.c`
9. `quectel_pdp_settings_set (240 B) — modem/src/cell_modem_quectel.c`
10. `at_command_request (176 B) — modem/src/cell_at.c`
11. `process_remaining_data (136 B) — modem/src/cell_at.c`
12. `urc_parse_unsolicited_response (16 B) — modem/src/cell_urc.c`
13. `parse_urc_crtdcp (1384 B) — modem/src/cell_urc.c`
14. `quectel_handle_urc_socket_incoming (16 B) — modem/src/cell_modem_quectel.c`
15. `socket_process_urc_incoming_connection (16 B) — cellular/src/cell_socket.c`
16. `socket_close_wrapper (16 B) — cellular/src/cell_socket.c`
17. `semtech_socket_close (24 B) — modem/src/cell_modem_semtech.c`
18. `tcp_delete (72 B) — modem/src/cell_modem_semtech.c`

### 17. 2816 B (18 frames)

1. `cell_task (16 B) — cellular/src/cell_task.c`
2. `process_message (8 B) — cellular/src/cell_task.c`
3. `connection_process (16 B) — cellular/src/cell_connect.c`
4. `perform_action (456 B) — cellular/src/cell_connect.c`
5. `start_registration (24 B) — cellular/src/cell_connect.c`
6. `check_operator_status (152 B) — cellular/src/cell_connect.c`
7. `execute_command (32 B) — cellular/src/cell_connect.c`
8. `config_pdp_wrapper (16 B) — cellular/src/cell_connect.c`
9. `quectel_pdp_settings_set (240 B) — modem/src/cell_modem_quectel.c`
10. `at_command_request (176 B) — modem/src/cell_at.c`
11. `process_remaining_data (136 B) — modem/src/cell_at.c`
12. `urc_parse_unsolicited_response (16 B) — modem/src/cell_urc.c`
13. `parse_urc_crtdcp (1384 B) — modem/src/cell_urc.c`
14. `semtech_handle_urc_ktcp_srvreq (16 B) — modem/src/cell_modem_semtech.c`
15. `socket_process_urc_incoming_connection (16 B) — cellular/src/cell_socket.c`
16. `socket_close_wrapper (16 B) — cellular/src/cell_socket.c`
17. `semtech_socket_close (24 B) — modem/src/cell_modem_semtech.c`
18. `tcp_close (72 B) — modem/src/cell_modem_semtech.c`

### 18. 2816 B (18 frames)

1. `cell_task (16 B) — cellular/src/cell_task.c`
2. `process_message (8 B) — cellular/src/cell_task.c`
3. `connection_process (16 B) — cellular/src/cell_connect.c`
4. `perform_action (456 B) — cellular/src/cell_connect.c`
5. `start_registration (24 B) — cellular/src/cell_connect.c`
6. `check_operator_status (152 B) — cellular/src/cell_connect.c`
7. `execute_command (32 B) — cellular/src/cell_connect.c`
8. `config_pdp_wrapper (16 B) — cellular/src/cell_connect.c`
9. `quectel_pdp_settings_set (240 B) — modem/src/cell_modem_quectel.c`
10. `at_command_request (176 B) — modem/src/cell_at.c`
11. `process_remaining_data (136 B) — modem/src/cell_at.c`
12. `urc_parse_unsolicited_response (16 B) — modem/src/cell_urc.c`
13. `parse_urc_crtdcp (1384 B) — modem/src/cell_urc.c`
14. `semtech_handle_urc_ktcp_srvreq (16 B) — modem/src/cell_modem_semtech.c`
15. `socket_process_urc_incoming_connection (16 B) — cellular/src/cell_socket.c`
16. `socket_close_wrapper (16 B) — cellular/src/cell_socket.c`
17. `semtech_socket_close (24 B) — modem/src/cell_modem_semtech.c`
18. `tcp_delete (72 B) — modem/src/cell_modem_semtech.c`

### 19. 2800 B (18 frames)

1. `cell_task (16 B) — cellular/src/cell_task.c`
2. `process_message (8 B) — cellular/src/cell_task.c`
3. `connection_process (16 B) — cellular/src/cell_connect.c`
4. `perform_action (456 B) — cellular/src/cell_connect.c`
5. `start_registration (24 B) — cellular/src/cell_connect.c`
6. `check_operator_status (152 B) — cellular/src/cell_connect.c`
7. `execute_command (32 B) — cellular/src/cell_connect.c`
8. `config_pdp_wrapper (16 B) — cellular/src/cell_connect.c`
9. `semtech_pdp_settings_set (16 B) — modem/src/cell_modem_semtech.c`
10. `define_pdp_context (232 B) — modem/src/cell_modem_semtech.c`
11. `at_command_request (176 B) — modem/src/cell_at.c`
12. `process_remaining_data (136 B) — modem/src/cell_at.c`
13. `urc_parse_unsolicited_response (16 B) — modem/src/cell_urc.c`
14. `parse_urc_crtdcp (1384 B) — modem/src/cell_urc.c`
15. `quectel_handle_urc_socket_incoming (16 B) — modem/src/cell_modem_quectel.c`
16. `socket_process_urc_incoming_connection (16 B) — cellular/src/cell_socket.c`
17. `socket_close_wrapper (16 B) — cellular/src/cell_socket.c`
18. `quectel_socket_close (72 B) — modem/src/cell_modem_quectel.c`

### 20. 2800 B (18 frames)

1. `cell_task (16 B) — cellular/src/cell_task.c`
2. `process_message (8 B) — cellular/src/cell_task.c`
3. `connection_process (16 B) — cellular/src/cell_connect.c`
4. `perform_action (456 B) — cellular/src/cell_connect.c`
5. `start_registration (24 B) — cellular/src/cell_connect.c`
6. `check_operator_status (152 B) — cellular/src/cell_connect.c`
7. `execute_command (32 B) — cellular/src/cell_connect.c`
8. `config_pdp_wrapper (16 B) — cellular/src/cell_connect.c`
9. `semtech_pdp_settings_set (16 B) — modem/src/cell_modem_semtech.c`
10. `define_pdp_context (232 B) — modem/src/cell_modem_semtech.c`
11. `at_command_request (176 B) — modem/src/cell_at.c`
12. `process_remaining_data (136 B) — modem/src/cell_at.c`
13. `urc_parse_unsolicited_response (16 B) — modem/src/cell_urc.c`
14. `parse_urc_crtdcp (1384 B) — modem/src/cell_urc.c`
15. `semtech_handle_urc_ktcp_srvreq (16 B) — modem/src/cell_modem_semtech.c`
16. `socket_process_urc_incoming_connection (16 B) — cellular/src/cell_socket.c`
17. `socket_close_wrapper (16 B) — cellular/src/cell_socket.c`
18. `quectel_socket_close (72 B) — modem/src/cell_modem_quectel.c`

## Recursive cycles

Representative cycles are listed below; recursion can be unbounded without a depth limit:
- `at_command_request` → `at_get_first_solicited_line` → `urc_parse_unsolicited_response` → `parse_urc_cdsi` → `quectel_handle_urc_socket_incoming` → `socket_process_urc_incoming_connection` → `socket_close_wrapper` → `quectel_socket_close` → `at_command_request`
- `at_command_request` → `at_get_first_solicited_line` → `urc_parse_unsolicited_response` → `parse_urc_cdsi` → `quectel_handle_urc_socket_incoming` → `socket_process_urc_incoming_connection` → `socket_close_wrapper` → `semtech_socket_close` → `get_tcp_socket_status` → `at_command_request`
- `at_command_request` → `at_get_first_solicited_line` → `urc_parse_unsolicited_response` → `parse_urc_cdsi` → `quectel_handle_urc_socket_incoming` → `socket_process_urc_incoming_connection` → `socket_close_wrapper` → `semtech_socket_close` → `tcp_close` → `at_command_request`
- `at_command_request` → `at_get_first_solicited_line` → `urc_parse_unsolicited_response` → `parse_urc_cdsi` → `quectel_handle_urc_socket_incoming` → `socket_process_urc_incoming_connection` → `socket_close_wrapper` → `semtech_socket_close` → `tcp_delete` → `at_command_request`

## Callgraph nodes without stack usage

- `at_parser_time_get` — `modem/src/cell_modem_common.c`
- `cell_cellular_info_get` — `cellular/src/cell_api.c`
- `cell_com_init` — `com/src/cell_com.c`
- `cell_com_notify_task_on_rxne` — `cellular/src/cell_task.c`
- `cell_com_set_reset_pin` — `com/src/cell_com.c`
- `cell_connect` — `cellular/src/cell_api.c`
- `cell_context_create` — `cellular/src/cell_api.c`
- `cell_dfota_abort` — `cellular/src/cell_api.c`
- `cell_dfota_activate` — `cellular/src/cell_api.c`
- `cell_dfota_start` — `cellular/src/cell_api.c`
- `cell_dfota_write` — `cellular/src/cell_api.c`
- `cell_driver_init` — `com/src/cell_driver_interface.c`
- `cell_driver_modem_reset` — `com/src/cell_driver_interface.c`
- `cell_driver_uart_irq_handler` — `com/src/cell_com.c`
- `cell_init` — `cellular/src/cell_api.c`
- `cell_log_config` — `cellular/src/cell_api.c`
- `cell_log_set_level` — `cellular/src/cell_log.c`
- `cell_modem_info_get` — `cellular/src/cell_api.c`
- `cell_network_info_get` — `cellular/src/cell_api.c`
- `cell_psm_settings_get` — `cellular/src/cell_api.c`
- `cell_service_status_get` — `cellular/src/cell_api.c`
- `cell_simcard_info_get` — `cellular/src/cell_api.c`
- `cell_socket_close` — `cellular/src/cell_api.c`
- `cell_socket_create` — `cellular/src/cell_api.c`
- `cell_socket_receive` — `cellular/src/cell_api.c`
- `cell_socket_send` — `cellular/src/cell_api.c`
- `cell_socket_verify_data` — `cellular/src/cell_api.c`
- `cell_test` — `cellular/src/cell_api.c`
- `cell_test_notify_custom_at` — `cellular/src/cell_test.c`
- `common_time_get` — `modem/src/cell_modem_common.c`
- `dfota_notify_activate` — `cellular/src/cell_dfota.c`
- `dfota_notify_cancel` — `cellular/src/cell_dfota.c`
- `dfota_notify_start` — `cellular/src/cell_dfota.c`
- `dfota_notify_write` — `cellular/src/cell_dfota.c`
- `monitoring_notify_get_cellular_info` — `cellular/src/cell_monitoring.c`
- `monitoring_notify_get_modem_info` — `cellular/src/cell_monitoring.c`
- `monitoring_notify_get_network_info` — `cellular/src/cell_monitoring.c`
- `monitoring_notify_get_psm_setting` — `cellular/src/cell_monitoring.c`
- `monitoring_notify_get_service_status` — `cellular/src/cell_monitoring.c`
- `monitoring_notify_get_simcard_info` — `cellular/src/cell_monitoring.c`
- `socket_notify_close` — `cellular/src/cell_socket.c`
- `socket_notify_create` — `cellular/src/cell_socket.c`
- `socket_notify_recv` — `cellular/src/cell_socket.c`
- `socket_notify_send` — `cellular/src/cell_socket.c`
- `socket_notify_verify_data` — `cellular/src/cell_socket.c`

## Ambiguous function matches

- `at_parser_time_get` — `modem/src/cell_modem_common.c`
- `cell_cellular_info_get` — `cellular/src/cell_api.c`
- `cell_com_init` — `com/src/cell_com.c`
- `cell_com_notify_task_on_rxne` — `cellular/src/cell_task.c`
- `cell_com_set_reset_pin` — `com/src/cell_com.c`
- `cell_connect` — `cellular/src/cell_api.c`
- `cell_context_create` — `cellular/src/cell_api.c`
- `cell_dfota_abort` — `cellular/src/cell_api.c`
- `cell_dfota_activate` — `cellular/src/cell_api.c`
- `cell_dfota_start` — `cellular/src/cell_api.c`
- `cell_dfota_write` — `cellular/src/cell_api.c`
- `cell_driver_init` — `com/src/cell_driver_interface.c`
- `cell_driver_modem_reset` — `com/src/cell_driver_interface.c`
- `cell_driver_uart_irq_handler` — `com/src/cell_com.c`
- `cell_init` — `cellular/src/cell_api.c`
- `cell_log_config` — `cellular/src/cell_api.c`
- `cell_log_set_level` — `cellular/src/cell_log.c`
- `cell_modem_info_get` — `cellular/src/cell_api.c`
- `cell_network_info_get` — `cellular/src/cell_api.c`
- `cell_psm_settings_get` — `cellular/src/cell_api.c`
- `cell_service_status_get` — `cellular/src/cell_api.c`
- `cell_simcard_info_get` — `cellular/src/cell_api.c`
- `cell_socket_close` — `cellular/src/cell_api.c`
- `cell_socket_create` — `cellular/src/cell_api.c`
- `cell_socket_receive` — `cellular/src/cell_api.c`
- `cell_socket_send` — `cellular/src/cell_api.c`
- `cell_socket_verify_data` — `cellular/src/cell_api.c`
- `cell_test` — `cellular/src/cell_api.c`
- `cell_test_notify_custom_at` — `cellular/src/cell_test.c`
- `common_time_get` — `modem/src/cell_modem_common.c`
- `dfota_notify_activate` — `cellular/src/cell_dfota.c`
- `dfota_notify_cancel` — `cellular/src/cell_dfota.c`
- `dfota_notify_start` — `cellular/src/cell_dfota.c`
- `dfota_notify_write` — `cellular/src/cell_dfota.c`
- `monitoring_notify_get_cellular_info` — `cellular/src/cell_monitoring.c`
- `monitoring_notify_get_modem_info` — `cellular/src/cell_monitoring.c`
- `monitoring_notify_get_network_info` — `cellular/src/cell_monitoring.c`
- `monitoring_notify_get_psm_setting` — `cellular/src/cell_monitoring.c`
- `monitoring_notify_get_service_status` — `cellular/src/cell_monitoring.c`
- `monitoring_notify_get_simcard_info` — `cellular/src/cell_monitoring.c`
- `socket_notify_close` — `cellular/src/cell_socket.c`
- `socket_notify_create` — `cellular/src/cell_socket.c`
- `socket_notify_recv` — `cellular/src/cell_socket.c`
- `socket_notify_send` — `cellular/src/cell_socket.c`
- `socket_notify_verify_data` — `cellular/src/cell_socket.c`
