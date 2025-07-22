#!/usr/bin/env python3
"""
Messaging Tracking and Analytics Demo
Showcases comprehensive message tracking capabilities
"""

from datetime import datetime, timedelta
import random

class MockMessageCampaign:
    """Mock campaign for demonstration"""
    def __init__(self, name, template_type, messages_sent):
        self.name = name
        self.template_type = template_type
        self.messages_sent = messages_sent
        
        # Simulate realistic metrics
        self.messages_delivered = int(messages_sent * random.uniform(0.92, 0.98))
        self.messages_failed = messages_sent - self.messages_delivered
        
        if template_type == 'email':
            self.messages_opened = int(self.messages_delivered * random.uniform(0.18, 0.35))
            self.messages_clicked = int(self.messages_opened * random.uniform(0.08, 0.25))
        elif template_type == 'sms':
            self.messages_opened = int(self.messages_delivered * random.uniform(0.85, 0.98))
            self.messages_clicked = int(self.messages_opened * random.uniform(0.15, 0.35))
        else:  # WhatsApp
            self.messages_opened = int(self.messages_delivered * random.uniform(0.75, 0.95))
            self.messages_clicked = int(self.messages_opened * random.uniform(0.12, 0.28))
        
        self.messages_bounced = random.randint(0, max(1, messages_sent // 50))
        self.unsubscribes = random.randint(0, max(1, messages_sent // 100))
        
        self.status = 'completed'
        self.sent_at = datetime.now() - timedelta(days=random.randint(1, 30))
    
    @property
    def delivery_rate(self):
        return round((self.messages_delivered / self.messages_sent) * 100, 2) if self.messages_sent > 0 else 0
    
    @property
    def open_rate(self):
        return round((self.messages_opened / self.messages_delivered) * 100, 2) if self.messages_delivered > 0 else 0
    
    @property
    def click_rate(self):
        return round((self.messages_clicked / self.messages_delivered) * 100, 2) if self.messages_delivered > 0 else 0
    
    @property
    def bounce_rate(self):
        return round((self.messages_bounced / self.messages_sent) * 100, 2) if self.messages_sent > 0 else 0

def generate_demo_campaigns():
    """Generate sample campaigns with realistic data"""
    campaigns = [
        MockMessageCampaign("Welcome Email Series", "email", 1250),
        MockMessageCampaign("SMS Product Launch", "sms", 3500),
        MockMessageCampaign("WhatsApp Order Updates", "whatsapp", 890),
        MockMessageCampaign("Newsletter - March 2025", "email", 5200),
        MockMessageCampaign("Flash Sale Alert", "sms", 2100),
        MockMessageCampaign("Payment Reminder", "whatsapp", 450),
        MockMessageCampaign("Customer Survey", "email", 1800),
        MockMessageCampaign("Appointment Confirmations", "sms", 680),
    ]
    return campaigns

def display_analytics_dashboard():
    """Display comprehensive analytics dashboard"""
    campaigns = generate_demo_campaigns()
    
    print("=== Cool Blue Messaging Analytics Dashboard ===\n")
    
    # Overall metrics
    total_sent = sum(c.messages_sent for c in campaigns)
    total_delivered = sum(c.messages_delivered for c in campaigns)
    total_opened = sum(c.messages_opened for c in campaigns)
    total_clicked = sum(c.messages_clicked for c in campaigns)
    total_failed = sum(c.messages_failed for c in campaigns)
    
    print(f"📊 OVERALL METRICS (Last 30 Days)")
    print(f"   📤 Messages Sent:     {total_sent:,}")
    print(f"   ✅ Messages Delivered: {total_delivered:,} ({(total_delivered/total_sent*100):.1f}%)")
    print(f"   📖 Messages Opened:   {total_opened:,} ({(total_opened/total_delivered*100):.1f}%)")
    print(f"   🖱️  Messages Clicked:   {total_clicked:,} ({(total_clicked/total_delivered*100):.1f}%)")
    print(f"   ❌ Messages Failed:    {total_failed:,} ({(total_failed/total_sent*100):.1f}%)")
    print()
    
    # Channel breakdown
    print(f"📱 CHANNEL PERFORMANCE")
    channels = {'email': [], 'sms': [], 'whatsapp': []}
    
    for campaign in campaigns:
        channels[campaign.template_type].append(campaign)
    
    for channel_name, channel_campaigns in channels.items():
        if not channel_campaigns:
            continue
            
        channel_sent = sum(c.messages_sent for c in channel_campaigns)
        channel_delivered = sum(c.messages_delivered for c in channel_campaigns)
        channel_opened = sum(c.messages_opened for c in channel_campaigns)
        channel_clicked = sum(c.messages_clicked for c in channel_campaigns)
        
        emoji = {'email': '📧', 'sms': '📱', 'whatsapp': '💬'}[channel_name]
        print(f"   {emoji} {channel_name.upper()}:")
        print(f"      Sent: {channel_sent:,} | Delivered: {(channel_delivered/channel_sent*100):.1f}% | Opened: {(channel_opened/channel_delivered*100):.1f}% | Clicked: {(channel_clicked/channel_delivered*100):.1f}%")
    print()
    
    # Campaign details
    print(f"🚀 RECENT CAMPAIGNS")
    campaigns_sorted = sorted(campaigns, key=lambda x: x.sent_at, reverse=True)
    
    for campaign in campaigns_sorted[:6]:
        status_emoji = {'completed': '✅', 'sending': '🔄', 'scheduled': '⏰', 'draft': '📝'}
        emoji = {'email': '📧', 'sms': '📱', 'whatsapp': '💬'}[campaign.template_type]
        
        print(f"   {emoji} {campaign.name}")
        print(f"      Status: {status_emoji.get(campaign.status, '❓')} {campaign.status.title()}")
        print(f"      Metrics: {campaign.messages_sent:,} sent • {campaign.delivery_rate}% delivered • {campaign.open_rate}% opened • {campaign.click_rate}% clicked")
        print(f"      Date: {campaign.sent_at.strftime('%B %d, %Y at %I:%M %p')}")
        print()
    
    print(f"🎯 KEY TRACKING FEATURES IMPLEMENTED:")
    print(f"   ✅ Real-time delivery status tracking")
    print(f"   ✅ Email open rate tracking with pixel beacons") 
    print(f"   ✅ Click-through rate monitoring with link tracking")
    print(f"   ✅ Bounce rate detection and management")
    print(f"   ✅ Unsubscribe tracking and compliance")
    print(f"   ✅ SMS delivery receipts from providers")
    print(f"   ✅ WhatsApp read receipts and delivery confirmations")
    print(f"   ✅ Campaign performance comparison")
    print(f"   ✅ Channel-specific optimization insights")
    print(f"   ✅ Error tracking with detailed failure reasons")
    print(f"   ✅ Geographic and device analytics")
    print(f"   ✅ A/B testing capabilities for templates")
    print(f"   ✅ Automated engagement scoring")
    print()
    
    # Engagement insights
    print(f"💡 ENGAGEMENT INSIGHTS:")
    best_email_open = max([c for c in campaigns if c.template_type == 'email'], key=lambda x: x.open_rate)
    best_sms_click = max([c for c in campaigns if c.template_type == 'sms'], key=lambda x: x.click_rate)
    
    print(f"   🏆 Best Email Open Rate: {best_email_open.name} ({best_email_open.open_rate}%)")
    print(f"   🏆 Best SMS Click Rate: {best_sms_click.name} ({best_sms_click.click_rate}%)")
    print(f"   📈 Average email open rate: {sum(c.open_rate for c in campaigns if c.template_type == 'email')/len([c for c in campaigns if c.template_type == 'email']):.1f}%")
    print(f"   📈 Average SMS engagement: {sum(c.open_rate for c in campaigns if c.template_type == 'sms')/len([c for c in campaigns if c.template_type == 'sms']):.1f}%")
    
    return campaigns

if __name__ == "__main__":
    display_analytics_dashboard()