{
    'name': 'Real Estate Management',
    'version': '1.1',
    'license': 'LGPL-3',
    'category': 'Website',
    'summary': 'Module for managing real estate properties and website integration',
    'description': 'Manage real estate properties with interactive map, listings, and contact forms.',
    'depends': ['base', 'base_geolocalize', 'web', 'website_sale', 'mail', 'base_setup'],
    'data': [
        # Security
        'security/ir.model.access.csv',
        'security/property_security.xml',

        # data
        'data/mail_property_rejection.xml',
        'data/sequences.xml',
        'data/agent_registration_demo.xml',
        'data/mail_activity.xml',
        # 'data/dashboard_data.xml',

        # Views
        'views/property_views.xml',
        'views/property_category_views.xml',
        'views/dashboard_menu.xml',
        'views/menu.xml',
        'views/property_registration_views.xml',
        'views/agent_views.xml',
        'views/agent_registration_views.xml',
        # 'views/portal_agent_views.xml',

        # Qweb Templates
        'views/qweb_templates/property_map_template.xml',
        'views/qweb_templates/property_detail_page.xml',
        'views/qweb_templates/properties_menu_page.xml',
        'views/qweb_templates/website_registration_template.xml',
        # 'views/qweb_templates/agent_directory_template.xml',
        # 'views/qweb_templates/agent_detail_template.xml',
        'views/qweb_templates/agent_registration_form_template.xml',
        'views/qweb_templates/agent_no_access.xml',
        'views/qweb_templates/agent_portal_dashboard.xml',
        'views/qweb_templates/agent_portal_profile.xml',
        'views/qweb_templates/agent_portal_property_form.xml',
        'views/qweb_templates/agent_portal_my_properties.xml',
        'views/qweb_templates/agent_portal_property_detail.xml',

        # wizards
        'wizard/agent_registration_reject_wizard_views.xml',

    ],
    'assets': {
        'web.assets_frontend': [
            'real_estate_management/static/src/js/property_map.js',
            # 'real_estate_management/static/src/css/property_map.css',
            # 'real_estate_management/static/src/css/agent_registration.css',
            # 'real_estate_management/static/src/css/dashboard.css',
            # 'real_estate_management/static/src/js/dashboard.js',

        ],
        'web.assets_backend': [
            'real_estate_management/static/src/css/dashboard.css',
            'real_estate_management/static/src/xml/dashboard.xml',
            'real_estate_management/static/src/js/dashboard.js',
            'https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js',
        ],
    },
    'installable': True,
    'application': True,
}
