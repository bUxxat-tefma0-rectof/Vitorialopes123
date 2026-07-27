async def generate_pix_full(self, query, db, user, amount):
    """
    Gera PIX completo com QR Code como imagem
    """
    from services.pix_service import PixService
    
    pix_service = PixService()
    resultado = pix_service.gerar_pix(user.id, amount, "Recarga de saldo")
    
    if not resultado['sucesso']:
        await query.edit_message_text(
            f"❌ Erro ao gerar PIX: {resultado.get('erro', 'Tente novamente')}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Voltar", callback_data='menu_recharge')]
            ])
        )
        pix_service.close()
        return
    
    bonus_pct = float(db.get_setting('bonus_percentage', '0'))
    bonus_min = float(db.get_setting('bonus_min_value', '0'))
    bonus = amount * (bonus_pct/100) if amount >= bonus_min and bonus_pct > 0 else 0
    
    # Enviar QR Code como imagem
    if resultado['qr_code_imagem']:
        caption = (
            f"💰 *Comprar Saldo com Pix Automático*\n\n"
            f"⏱️ Expira em: {resultado['expiracao_minutos']} Minutos\n"
            f"💵 Valor: R$ {amount:.2f}\n"
            f"✨ ID da Recarga: {resultado['pix_id']}\n\n"
            f"📃 Atenção: Este código é válido para apenas um único pagamento.\n\n"
            f"💎 Pix Copia e Cola:\n"
            f"`{resultado['copia_cola']}`\n\n"
            f"💡 Dica: Clique no código acima para copiar.\n\n"
            f"📊 Dados:\n"
            f"— 💰 Saldo Atual: R$ {user.balance:.2f}\n"
        )
        
        if bonus > 0:
            caption += f"— 🎁 Bônus à receber: R$ {bonus:.2f}\n"
            caption += f"— 💸 Saldo após o pagamento: R$ {user.balance + amount + bonus:.2f}\n"
        else:
            caption += f"— 💸 Saldo após o pagamento: R$ {user.balance + amount:.2f}\n"
        
        caption += "\n🇧🇷 Após o pagamento, seu saldo será liberado instantaneamente."
        
        keyboard = [
            [InlineKeyboardButton("🔄 Aguardando Pagamento", callback_data=f'pix_check_{resultado["pix_id"]}')],
            [InlineKeyboardButton("📋 Copiar PIX", callback_data=f'pix_copy_{resultado["pix_id"]}')]
        ]
        
        await query.message.reply_photo(
            photo=resultado['qr_code_imagem'],
            caption=caption,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
        
        await query.edit_message_text(
            "💳 PIX gerado! Confira a imagem acima.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Voltar ao Menu", callback_data='back_main')]
            ])
        )
    else:
        # Fallback sem imagem
        text = (
            f"💰 PIX Gerado\n\n"
            f"💵 Valor: R$ {amount:.2f}\n"
            f"⏰ Expira em: {resultado['expiracao_minutos']} min\n"
            f"🆔 ID: {resultado['pix_id']}\n\n"
            f"📋 Copia e Cola:\n`{resultado['copia_cola']}`"
        )
        
        keyboard = [
            [InlineKeyboardButton("Verificar Pagamento", callback_data=f'pix_check_{resultado["pix_id"]}')],
            [InlineKeyboardButton("Voltar", callback_data='menu_recharge')]
        ]
        
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    pix_service.close()
