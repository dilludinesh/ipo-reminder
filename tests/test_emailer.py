"""Tests for the emailer module."""
import pytest
from unittest.mock import AsyncMock, patch
from email.mime.multipart import MIMEMultipart

class TestEmailer:
    """Test cases for the Emailer class."""
    
    @pytest.fixture
    def emailer(self):
        """Create an Emailer instance with test configuration."""
        with patch('smtplib.SMTP_SSL') as mock_smtp:
            emailer = Emailer(
                smtp_server="smtp.example.com",
                smtp_port=465,
                username="test@example.com",
                password="testpass",
                from_email="noreply@example.com"
            )
            emailer.server = mock_smtp.return_value
            yield emailer
    
    @pytest.mark.asyncio
    async def test_send_email_success(self, emailer):
        """Test sending an email successfully."""
        # Configure the mock SMTP server
        emailer.server.send_message = AsyncMock()
        
        # Send a test email
        result = await emailer.send_email(
            to="recipient@example.com",
            subject="Test Subject",
            html_content="<p>Test email content</p>",
            text_content="Test email content"
        )
        
        # Verify the email was sent
        assert result is True
        emailer.server.send_message.assert_awaited_once()
        
        # Verify the email content
        sent_msg = emailer.server.send_message.call_args[0][0]
        assert sent_msg['From'] == "noreply@example.com"
        assert sent_msg['To'] == "recipient@example.com"
        assert sent_msg['Subject'] == "Test Subject"
        assert "<p>Test email content</p>" in sent_msg.as_string()
        
    @pytest.mark.asyncio
    async def test_send_email_with_attachments(self, emailer):
        """Test sending an email with attachments."""
        emailer.server.send_message = AsyncMock()
        
        # Create a test attachment
        attachments = [
            {
                'content': b'Test attachment content',
                'filename': 'test.txt',
                'mimetype': 'text/plain'
            }
        ]
        
        # Send email with attachment
        result = await emailer.send_email(
            to="recipient@example.com",
            subject="Test Email with Attachment",
            html_content="<p>Email with attachment</p>",
            text_content="Email with attachment",
            attachments=attachments
        )
        
        assert result is True
        emailer.server.send_message.assert_awaited_once()
        
    @pytest.mark.asyncio
    async def test_send_email_failure(self, emailer):
        """Test email sending failure."""
        # Configure the mock to raise an exception
        emailer.server.send_message.side_effect = Exception("SMTP Error")
        
        # Attempt to send an email
        result = await emailer.send_email(
            to="recipient@example.com",
            subject="Test Failure",
            html_content="<p>This should fail</p>",
            text_content="This should fail"
        )
        
        # Verify the failure was handled
        assert result is False
        
    @pytest.mark.asyncio
    async def test_send_ipo_notification(self, emailer):
        """Test sending an IPO notification email."""
        emailer.server.send_message = AsyncMock()
        
        # Create a sample IPO
        ipo_data = {
            'name': 'Test IPO',
            'symbol': 'TST',
            'price_range': '100-110',
            'lot_size': 15,
            'issue_date': '2023-11-01',
            'close_date': '2023-11-10',
            'listing_date': '2023-11-20',
            'min_investment': 15000,
            'source': 'test_source',
            'url': 'http://example.com/ipo/test',
        }
        
        # Send the notification
        result = await emailer.send_ipo_notification(
            to="recipient@example.com",
            ipo_data=ipo_data,
            recommendation="subscribe",
            analysis="Strong fundamentals and growth potential"
        )
        
        assert result is True
        emailer.server.send_message.assert_awaited_once()
        
        # Verify the email content
        sent_msg = emailer.server.send_message.call_args[0][0]
        assert "Test IPO (TST)" in sent_msg['Subject']
        assert "100-110" in sent_msg.as_string()
        assert "Strong fundamentals" in sent_msg.as_string()
        
    @pytest.mark.asyncio
    async def test_close_connection(self, emailer):
        """Test closing the email connection."""
        emailer.server.quit = AsyncMock()
        
        await emailer.close()
        
        emailer.server.quit.assert_awaited_once()
