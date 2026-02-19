from odoo import http, fields
from odoo.http import request
import json
from odoo.tools.json import scriptsafe as json_scriptsafe
import base64
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class RealEstateController(http.Controller):

    # ─────────────────────────────────────────────────────────────
    # NEW ENDPOINT  ← THIS IS THE KEY ADDITION
    # Called by property_map.js via fetch('/api/investment-news?city=...')
    # Returns plain JSON — no template needed
    # ─────────────────────────────────────────────────────────────
    @http.route('/api/investment-news', type='http', auth='public', website=True, methods=['GET'], csrf=False)
    def api_investment_news(self, **kwargs):
        city = kwargs.get('city', '').strip()
        Property = request.env['property.property'].sudo()

        news = ''
        try:
            if city:
                news = Property.get_daily_investment_news(city)
                _logger.info(f'[API] City news for "{city}": {len(news)} chars')
            else:
                news = Property.get_trending_investment_news()
                _logger.info(f'[API] Trending news: {len(news)} chars')
        except Exception as e:
            _logger.error(f'[API] News fetch error: {e}')
            news = ''

        result = json.dumps({'city': city, 'news': news})
        return request.make_response(
            result,
            headers=[
                ('Content-Type', 'application/json'),
                ('Cache-Control', 'no-cache, no-store'),
            ]
        )

    # ─────────────────────────────────────────────────────────────
    # MAIN MAP PAGE  (unchanged)
    # ─────────────────────────────────────────────────────────────
    @http.route('/', type='http', auth='public', website=True)
    def property_map(self, **kwargs):

        Property = request.env['property.property'].sudo()
        selected_city = kwargs.get('city', '')
        all_properties = Property.search([('is_published', '=', True)])
        city_list = sorted(list(set([p.city for p in all_properties if p.city])))

        search_domain = [
            ('is_published', '=', True),
            ('latitude', '!=', False),
            ('longitude', '!=', False)
        ]
        if selected_city:
            search_domain.append(('city', '=', selected_city))

        properties = Property.search(search_domain)

        featured_domain = [('is_published', '=', True), ('is_featured', '=', True)]
        if selected_city:
            featured_domain.append(('city', '=', selected_city))
        featured_properties = Property.search(featured_domain)

        city_investment_info = None
        if selected_city:
            city_investment_info = Property.get_city_investment_info(selected_city)

        palette = ["#059669", "#dc2626", "#7c3aed", "#ea580c", "#2563eb", "#d97706", "#0891b2", "#9333ea"]
        category_colors = {}
        idx = 0

        property_data = []
        for prop in properties:
            if prop.latitude and prop.longitude:
                cat = prop.category_id.name if prop.category_id else 'Property'
                if cat not in category_colors:
                    category_colors[cat] = palette[idx % len(palette)]
                    idx += 1

                image_url = None
                if prop.image:
                    image_url = f"data:image/png;base64,{prop.image.decode('utf-8')}"
                elif prop.gallery_image_ids:
                    first_image = prop.gallery_image_ids[0]
                    if first_image.datas:
                        image_url = f"data:image/png;base64,{first_image.datas.decode('utf-8')}"

                full_address = ", ".join(filter(None, [prop.street, prop.city, prop.zip_code]))

                property_data.append({
                    'id': prop.id,
                    'name': prop.name or '',
                    'latitude': float(prop.latitude),
                    'longitude': float(prop.longitude),
                    'street': prop.street or '',
                    'city': prop.city or '',
                    'zip_code': prop.zip_code or '',
                    'price': float(prop.price) if prop.price else 0,
                    'contact_phone': prop.contact_phone or '',
                    'contact_email': prop.contact_email or '',
                    'contact_name': prop.contact_name or '',
                    'short_description': prop.short_description or '',
                    'image_url': image_url,
                    'property_type': cat,
                    'nearby_landmarks': prop.nearby_landmarks or '',
                    'views': prop.views or 0,
                    'seo_title': prop.seo_title or '',
                    'marker_color': category_colors[cat],
                    'full_address': full_address,
                })

        _logger.info(f"🎯 RENDER - City: '{selected_city}', Properties: {len(property_data)}")

        return request.render('real_estate_management.property_map_template', {
            'property_count': len(property_data),
            'properties_json': json_scriptsafe.dumps(property_data) if property_data else '[]',
            'category_colors': json_scriptsafe.dumps(category_colors),
            'city_list': city_list,
            'selected_city': selected_city,
            'featured_properties': featured_properties,
            'city_investment_info': city_investment_info,
        })

    # ─────────────────────────────────────────────────────────────
    # PROPERTY DETAIL
    # ─────────────────────────────────────────────────────────────
    @http.route('/property/<int:property_id>', type='http', auth='public', website=True)
    def property_detail(self, property_id, **kwargs):
        prop = request.env['property.property'].sudo().browse(property_id)
        if not prop.exists() or not prop.is_published:
            return request.not_found()
        if not prop.ai_content_generated:
            try:
                prop.generate_ai_content()
            except Exception as e:
                _logger.error(f"Failed to generate AI content for property {prop.id}: {e}")
        try:
            prop.write({'views': prop.views + 1})
        except Exception as e:
            _logger.error(f"Failed to update views for property {prop.id}: {e}")
        return request.render('real_estate_management.property_detail_page', {
            'property': prop,
        })

    # ─────────────────────────────────────────────────────────────
    # PROPERTY LISTING
    # ─────────────────────────────────────────────────────────────
    @http.route('/properties', type='http', auth='public', website=True)
    def property_listing(self, **kwargs):
        search = kwargs.get('search', '')
        city = kwargs.get('city', '')
        zip_code = kwargs.get('zip_code', '')

        domain = [('is_published', '=', True), ('status', '!=', 'sold')]
        if search:
            domain += ['|', '|',
                       ('name', 'ilike', search),
                       ('city', 'ilike', search),
                       ('zip_code', 'ilike', search)]
        if city:
            domain.append(('city', 'ilike', city))
        if zip_code:
            domain.append(('zip_code', 'ilike', zip_code))

        properties = request.env['property.property'].sudo().search(domain)

        property_card_data = []
        for prop in properties:
            property_card_data.append({
                'id': prop.id,
                'name': prop.name,
                'image_url': f"data:image/png;base64,{prop.image.decode('utf-8')}" if prop.image else '',
                'category': prop.category_id.name or '',
                'price': prop.price,
                'plot_area': prop.plot_area,
                'price_per_sqft': prop.price_per_sqft,
                'city': prop.city,
                'zip_code': prop.zip_code,
                'status': prop.status,
                'status_ribbon_html': prop.status_ribbon_html,
            })

        return request.render('real_estate_management.property_listing_template', {
            'properties': property_card_data,
            'search': search,
            'city': city,
            'zip_code': zip_code,
        })

    # ─────────────────────────────────────────────────────────────
    # PROPERTY REGISTRATION
    # ─────────────────────────────────────────────────────────────
    # @http.route('/property/register', type='http', auth='public', website=True)
    # def show_registration_form(self, **kwargs):
    #     return request.render('real_estate_management.property_registration_form')

    @http.route('/property/register', type='http', auth='public', website=True)
    def show_registration_form(self, **kwargs):

        india = request.env['res.country'].sudo().search([('code', '=', 'IN')], limit=1)
        states = request.env['res.country.state'].sudo().search(
            [('country_id', '=', india.id)],
            order="name asc"
        )

        return request.render('real_estate_management.property_registration_form', {
            'states': states
        })

    @http.route('/property/submit', type='http', auth='public', website=True, csrf=False)
    def submit_registration(self, **post):
        try:
            upload_files = request.httprequest.files.getlist('images')
            aadhar_file = request.httprequest.files.get('aadhar_document')
            agreement_file = request.httprequest.files.get('agreement_document')

            property_vals = {
                'customer_name': post.get('customer_name'),
                'property_name': post.get('property_name'),
                'phone_number': post.get('phone_number'),
                'facing_direction': post.get('facing_direction'),
                'place': post.get('place'),
                'category': post.get('category'),
                'sq_yards': post.get('sq_yards'),
                'price': post.get('price'),
                'location': post.get('location'),
                'city': post.get('city'),
                'state_id': int(post.get('state_id')) if post.get('state_id') else False,
                'status': 'submitted',
            }

            property_rec = request.env['property.registration'].sudo().create(property_vals)
            property_rec._send_admin_notification()

            for idx, file in enumerate(upload_files):
                content = base64.b64encode(file.read())
                if idx == 0:
                    property_rec.image = content
                else:
                    request.env['ir.attachment'].sudo().create({
                        'name': file.filename,
                        'res_model': 'property.registration',
                        'res_id': property_rec.id,
                        'type': 'binary',
                        'datas': content,
                        'mimetype': file.content_type,
                    })

            if aadhar_file:
                property_rec.aadhar_document = base64.b64encode(aadhar_file.read())
                property_rec.aadhar_filename = aadhar_file.filename

            if agreement_file:
                property_rec.agreement_document = base64.b64encode(agreement_file.read())
                property_rec.agreement_filename = agreement_file.filename

            return request.render('real_estate_management.property_submission_success')

        except Exception as e:
            _logger.exception("Error in property registration")
            return request.render('real_estate_management.property_submission_error', {'error': str(e)})

    # ─────────────────────────────────────────────────────────────
    # AGENT REGISTRATION
    # ─────────────────────────────────────────────────────────────
    @http.route('/agent/register', type='http', auth='public', website=True)
    def agent_registration_form(self, **kwargs):
        categories = request.env['property.category'].sudo().search([])
        states = request.env['res.country.state'].sudo().search([
            ('country_id', '=', request.env.company.country_id.id)
        ], order='name')
        return request.render('real_estate_management.agent_registration_form_template', {
            'categories': categories,
            'states': states,
        })

    @http.route('/agent/register/submit', type='http', auth='public', website=True, csrf=False, methods=['POST'])
    def submit_agent_registration(self, **post):
        try:
            profile_image = request.httprequest.files.get('profile_image')
            id_proof = request.httprequest.files.get('id_proof')
            license_doc = request.httprequest.files.get('license_document')
            resume = request.httprequest.files.get('resume')
            portfolio_images = request.httprequest.files.getlist('portfolio_images')

            registration_vals = {
                'agent_name': post.get('agent_name'),
                'email': post.get('email'),
                'phone': post.get('phone'),
                'whatsapp': post.get('whatsapp'),
                'designation': post.get('designation'),
                'expertise_level': post.get('expertise_level'),
                'license_number': post.get('license_number'),
                'experience_years': int(post.get('experience_years', 0)),
                'city': post.get('city'),
                'state_id': int(post.get('state_id')),
                'zip_code': post.get('zip_code'),
                'short_bio': post.get('short_bio'),
                'detailed_bio': post.get('detailed_bio'),
                'qualifications': post.get('qualifications'),
                'languages_spoken': post.get('languages_spoken', 'English, Hindi'),
                'linkedin_url': post.get('linkedin_url'),
                'facebook_url': post.get('facebook_url'),
                'status': 'submitted',
            }

            if profile_image:
                registration_vals['profile_image'] = base64.b64encode(profile_image.read())
            if id_proof:
                registration_vals['id_proof'] = base64.b64encode(id_proof.read())
                registration_vals['id_proof_filename'] = id_proof.filename
            if license_doc:
                registration_vals['license_document'] = base64.b64encode(license_doc.read())
                registration_vals['license_filename'] = license_doc.filename
            if resume:
                registration_vals['resume'] = base64.b64encode(resume.read())
                registration_vals['resume_filename'] = resume.filename

            specialization_ids = request.httprequest.form.getlist('specialization_ids')
            if specialization_ids:
                registration_vals['specialization_ids'] = [(6, 0, [int(sid) for sid in specialization_ids])]

            registration = request.env['agent.registration'].sudo().create(registration_vals)
            registration._send_admin_notification()

            for idx, img_file in enumerate(portfolio_images):
                if img_file:
                    attachment = request.env['ir.attachment'].sudo().create({
                        'name': f'Portfolio_{idx + 1}_{img_file.filename}',
                        'res_model': 'agent.registration',
                        'res_id': registration.id,
                        'type': 'binary',
                        'datas': base64.b64encode(img_file.read()),
                        'mimetype': img_file.content_type,
                    })
                    registration.attachment_ids = [(4, attachment.id)]

            _logger.info(f"Agent registration submitted: {registration.agent_name}")
            return request.render('real_estate_management.agent_registration_success_template', {
                'registration': registration,
            })

        except Exception as e:
            _logger.exception("Error in agent registration submission")
            return request.render('real_estate_management.agent_registration_error_template', {
                'error': str(e)
            })
