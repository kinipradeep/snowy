#!/usr/bin/env python3
"""
Messaging Analytics and Tracking System
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from datetime import datetime, timedelta
from models import MessageCampaign, MessageDelivery, Template, Contact, Group
from utils import login_required, organization_required, get_current_organization
from app import db
import json

analytics_bp = Blueprint('analytics', __name__)

@analytics_bp.route('/dashboard')
@login_required
@organization_required
def analytics_dashboard():
    """Main analytics dashboard showing messaging metrics"""
    organization = get_current_organization()
    
    # Get time period from query params (default: last 30 days)
    period = request.args.get('period', '30')
    
    if period == '7':
        start_date = datetime.utcnow() - timedelta(days=7)
    elif period == '30':
        start_date = datetime.utcnow() - timedelta(days=30)
    elif period == '90':
        start_date = datetime.utcnow() - timedelta(days=90)
    else:
        start_date = datetime.utcnow() - timedelta(days=365)
    
    # Get campaigns in the time period
    campaigns = MessageCampaign.query.filter(
        MessageCampaign.organization_id == organization.id,
        MessageCampaign.created_at >= start_date
    ).order_by(MessageCampaign.created_at.desc()).all()
    
    # Calculate overall metrics
    total_sent = sum(c.messages_sent for c in campaigns)
    total_delivered = sum(c.messages_delivered for c in campaigns)
    total_opened = sum(c.messages_opened for c in campaigns)
    total_clicked = sum(c.messages_clicked for c in campaigns)
    total_failed = sum(c.messages_failed for c in campaigns)
    
    # Calculate rates
    delivery_rate = round((total_delivered / total_sent * 100) if total_sent > 0 else 0, 2)
    open_rate = round((total_opened / total_delivered * 100) if total_delivered > 0 else 0, 2)
    click_rate = round((total_clicked / total_delivered * 100) if total_delivered > 0 else 0, 2)
    
    # Channel breakdown
    channel_stats = {}
    for campaign in campaigns:
        channel = campaign.template.template_type
        if channel not in channel_stats:
            channel_stats[channel] = {
                'sent': 0, 'delivered': 0, 'opened': 0, 'clicked': 0
            }
        channel_stats[channel]['sent'] += campaign.messages_sent
        channel_stats[channel]['delivered'] += campaign.messages_delivered
        channel_stats[channel]['opened'] += campaign.messages_opened
        channel_stats[channel]['clicked'] += campaign.messages_clicked
    
    # Recent deliveries with issues
    failed_deliveries = MessageDelivery.query.filter(
        MessageDelivery.campaign_id.in_([c.id for c in campaigns]),
        MessageDelivery.status.in_(['failed', 'bounced'])
    ).order_by(MessageDelivery.updated_at.desc()).limit(10).all()
    
    return render_template('analytics/dashboard.html',
                         campaigns=campaigns[:10],  # Latest 10 campaigns
                         total_sent=total_sent,
                         total_delivered=total_delivered,
                         total_opened=total_opened,
                         total_clicked=total_clicked,
                         total_failed=total_failed,
                         delivery_rate=delivery_rate,
                         open_rate=open_rate,
                         click_rate=click_rate,
                         channel_stats=channel_stats,
                         failed_deliveries=failed_deliveries,
                         period=period)

@analytics_bp.route('/campaign/<int:campaign_id>')
@login_required
@organization_required
def campaign_details(campaign_id):
    """Detailed view of a specific campaign"""
    organization = get_current_organization()
    
    campaign = MessageCampaign.query.filter_by(
        id=campaign_id,
        organization_id=organization.id
    ).first_or_404()
    
    # Get delivery details
    deliveries = MessageDelivery.query.filter_by(
        campaign_id=campaign.id
    ).order_by(MessageDelivery.created_at.desc()).all()
    
    # Group deliveries by status
    status_counts = {}
    for delivery in deliveries:
        status = delivery.status
        if status not in status_counts:
            status_counts[status] = 0
        status_counts[status] += 1
    
    # Timeline data (daily breakdown)
    timeline_data = {}
    for delivery in deliveries:
        if delivery.sent_at:
            date_key = delivery.sent_at.strftime('%Y-%m-%d')
            if date_key not in timeline_data:
                timeline_data[date_key] = {'sent': 0, 'delivered': 0, 'opened': 0}
            timeline_data[date_key]['sent'] += 1
            if delivery.delivered_at:
                timeline_data[date_key]['delivered'] += 1
            if delivery.opened_at:
                timeline_data[date_key]['opened'] += 1
    
    return render_template('analytics/campaign_details.html',
                         campaign=campaign,
                         deliveries=deliveries[:100],  # Show first 100
                         status_counts=status_counts,
                         timeline_data=timeline_data)

@analytics_bp.route('/track/open/<delivery_id>')
def track_open(delivery_id):
    """Track email open (pixel tracking)"""
    delivery = MessageDelivery.query.get_or_404(delivery_id)
    
    if not delivery.opened_at:
        delivery.opened_at = datetime.utcnow()
        delivery.campaign.messages_opened += 1
        db.session.commit()
    
    # Return a 1x1 transparent pixel
    from flask import Response
    pixel = b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\x00\x00\x00\x21\xF9\x04\x01\x00\x00\x00\x00\x2C\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x04\x01\x00\x3B'
    return Response(pixel, mimetype='image/gif')

@analytics_bp.route('/track/click/<delivery_id>')
def track_click(delivery_id):
    """Track link clicks"""
    delivery = MessageDelivery.query.get_or_404(delivery_id)
    
    if not delivery.clicked_at:
        delivery.clicked_at = datetime.utcnow()
        delivery.campaign.messages_clicked += 1
        db.session.commit()
    
    # Redirect to the actual URL (should be passed as parameter)
    target_url = request.args.get('url', 'https://example.com')
    return redirect(target_url)

@analytics_bp.route('/api/metrics')
@login_required
@organization_required
def api_metrics():
    """API endpoint for real-time metrics"""
    organization = get_current_organization()
    
    # Get last 30 days of data
    start_date = datetime.utcnow() - timedelta(days=30)
    
    campaigns = MessageCampaign.query.filter(
        MessageCampaign.organization_id == organization.id,
        MessageCampaign.created_at >= start_date
    ).all()
    
    metrics = {
        'total_campaigns': len(campaigns),
        'total_sent': sum(c.messages_sent for c in campaigns),
        'total_delivered': sum(c.messages_delivered for c in campaigns),
        'total_opened': sum(c.messages_opened for c in campaigns),
        'total_clicked': sum(c.messages_clicked for c in campaigns),
        'channels': {}
    }
    
    # Channel breakdown
    for campaign in campaigns:
        channel = campaign.template.template_type
        if channel not in metrics['channels']:
            metrics['channels'][channel] = {
                'sent': 0, 'delivered': 0, 'opened': 0, 'clicked': 0
            }
        metrics['channels'][channel]['sent'] += campaign.messages_sent
        metrics['channels'][channel]['delivered'] += campaign.messages_delivered
        metrics['channels'][channel]['opened'] += campaign.messages_opened
        metrics['channels'][channel]['clicked'] += campaign.messages_clicked
    
    return jsonify(metrics)

def create_demo_campaign():
    """Create a demo campaign with sample data for testing"""
    from app import create_app
    app = create_app()
    
    with app.app_context():
        # Create a sample campaign
        template = Template.query.filter_by(template_type='email').first()
        if template:
            campaign = MessageCampaign(
                name='Welcome Email Campaign',
                description='Demo campaign for new user onboarding',
                template_id=template.id,
                organization_id=1,
                status='completed',
                messages_sent=150,
                messages_delivered=145,
                messages_opened=89,
                messages_clicked=23,
                messages_failed=5,
                sent_at=datetime.utcnow() - timedelta(days=3),
                completed_at=datetime.utcnow() - timedelta(days=2)
            )
            db.session.add(campaign)
            db.session.commit()
            print(f"✅ Created demo campaign: {campaign.name}")
            return campaign.id
    
    return None

if __name__ == "__main__":
    print("=== Message Analytics Demo ===")
    campaign_id = create_demo_campaign()
    if campaign_id:
        print(f"Demo campaign created with ID: {campaign_id}")
        print("Metrics available at: /analytics/dashboard")
        print(f"Campaign details at: /analytics/campaign/{campaign_id}")