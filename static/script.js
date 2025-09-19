        console.log("script.js carregado!");
// Variável global para armazenar o ID do intervalo
        let paymentIntervalId;

        // Função para verificar o status da transação
        async function checkPaymentStatus(transactionId) {
            console.log("checkPaymentStatus foi chamada com transactionId:", transactionId);
            // Limpa qualquer intervalo existente para evitar múltiplos polls
            if (paymentIntervalId) {
                clearInterval(paymentIntervalId);
            }

            const performStatusCheck = async () => {
                try {
                    const response = await fetch(`/payment_status/${transactionId}`);
                    const data = await response.json();

                    console.log("Verificando status da transação:", data);

                    if (response.ok) {
                        const statusMessage = document.getElementById("statusMessage");
                        const statusText = data.status;
                        
                        if (statusText === "PENDENTE") {
                            statusMessage.innerHTML = '<i class="fas fa-clock" style="margin-right: 8px;"></i>Aguardando pagamento...';
                        } else if (statusText === "PAGO") {
                            statusMessage.innerHTML = '<i class="fas fa-check-circle" style="margin-right: 8px; color: #48bb78;"></i>Pagamento confirmado!';
                            showNotification("Pagamento confirmado! ✅", "success");
                            clearInterval(paymentIntervalId); // Parar a verificação do status após o pagamento
                        } else {
                            statusMessage.innerHTML = `<i class="fas fa-info-circle" style="margin-right: 8px;"></i>Status: ${statusText}`;
                        }
                    } else {
                        document.getElementById("statusMessage").innerHTML = '<i class="fas fa-exclamation-triangle" style="margin-right: 8px;"></i>Erro ao verificar status';
                    }
                } catch (error) {
                    console.error("Erro ao verificar status:", error);
                }
            };

            // Executa a verificação imediatamente e depois a cada 5 segundos
            performStatusCheck();
            paymentIntervalId = setInterval(performStatusCheck, 5000);

            // Adicionando funcionalidade de verificação manual
            document.getElementById("checkPaymentStatusBtn").onclick = async () => {
                clearInterval(paymentIntervalId); // Parar a verificação automática atual
                await performStatusCheck(); // Realiza uma verificação manual
                paymentIntervalId = setInterval(performStatusCheck, 5000); // Reinicia o polling
            };
        }

        // Função para copiar o código PIX
        function copyPixCode() {
            var copyText = document.getElementById("pixCode");
            copyText.select();
            copyText.setSelectionRange(0, 99999); // Para dispositivos móveis
            
            try {
                document.execCommand("copy");
                showNotification("Código PIX copiado com sucesso! 📋", "success");
            } catch (err) {
                showNotification("Erro ao copiar código PIX", "error");
            }
        }

        // Função para mostrar notificações
        function showNotification(message, type = "info") {
            const notification = document.createElement('div');
            notification.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                padding: 15px 20px;
                border-radius: 10px;
                color: white;
                font-weight: 600;
                z-index: 1000;
                animation: slideInRight 0.3s ease-out;
                max-width: 300px;
            `;
            
            if (type === "success") {
                notification.style.background = "linear-gradient(135deg, #48bb78, #38a169)";
            } else if (type === "error") {
                notification.style.background = "linear-gradient(135deg, #f56565, #e53e3e)";
            } else {
                notification.style.background = "linear-gradient(135deg, #667eea, #764ba2)";
            }
            
            notification.textContent = message;
            document.body.appendChild(notification);
            
            setTimeout(() => {
                notification.style.animation = "slideOutRight 0.3s ease-in";
                setTimeout(() => {
                    document.body.removeChild(notification);
                }, 300);
            }, 3000);
        }

        // Enviar a requisição para criar o depósito
        document.getElementById("depositForm").addEventListener("submit", async function (event) {
            console.log("Evento submit do formulário disparado.");
            event.preventDefault();

            const amount = document.getElementById("amount").value;
            const description = document.getElementById("description").value;
            const createBtn = document.getElementById("createBtn");
            
            // Adicionar loading
            const originalText = createBtn.innerHTML;
            createBtn.innerHTML = '<i class="fas fa-spinner fa-spin" style="margin-right: 8px;"></i>Gerando QR Code...';
            createBtn.disabled = true;

            console.log("Enviando dados para o backend:", { amount, description });

            try {
                const response = await fetch("/create_deposit", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                    },
                    body: JSON.stringify({ amount, description }),
                });

                const data = await response.json();
                console.log("Resposta recebida do backend:", data);

                if (response.ok) {
                    // Exibe o QR Code e o código PIX
                    document.getElementById("qrCodeContainer").style.display = "block";
                    document.getElementById("qrCode").src = data.qr_code_url;
                    document.getElementById("pixCode").value = data.pix_code;

                    // Exibe a área de status
                    document.getElementById("statusContainer").style.display = "block";
                    document.getElementById("infoContainer").style.display = "block";

                    // Verifica o status da transação após a criação
                    console.log("Iniciando verificação de status para transactionId:", data.transaction_id);
                    checkPaymentStatus(data.transaction_id);  // Começar a verificar automaticamente
                    
                    showNotification("QR Code gerado com sucesso! 🎉", "success");
                } else {
                    showNotification("Erro ao gerar QR Code: " + data.message, "error");
                }
            } catch (error) {
                console.error("Erro na requisição:", error);
                showNotification("Erro de conexão. Tente novamente.", "error");
            } finally {
                // Restaurar botão
                createBtn.innerHTML = originalText;
                createBtn.disabled = false;
            }
        });

