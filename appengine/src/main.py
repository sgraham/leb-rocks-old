import webapp2
from google.appengine.ext import ndb

import model


main_key = ndb.Key('LebRocks', 'fundraising')


class MainPage(webapp2.RequestHandler):
  def get(self):
    self.response.headers['Content-Type'] = 'text/plain'
    self.response.write('Hello, World!')


class TestData(webapp2.RequestHandler):
  def get(self):
    division16 = model.Division(
        parent=main_key,
        division_name='16',
        teacher_name='Gabriela Novotny',
        classroom='102')
    division16.put()

    s = model.Student(
        parent=main_key, name='Madeline Graham', division=division16.key)
    s.put()

    s = model.Student(
        parent=main_key, name='Nola Taylor', division=division16.key)
    s.put()

    i = model.Item(
        parent=main_key,
        price_in_cents=2000,
        name='Emergency Comfort Kit',
        description='Stuff and things and more stuff.',
        image_name='todo.jpg')
    i.put()

    self.response.headers['Content-Type'] = 'text/plain'
    self.response.write('Test data splorped.')


class TestMakeOrder(webapp2.RequestHandler):
  def get(self):

    my_order = model.Order(
        model.ItemInstance(count=1, item=emergency_kit.key))


app = webapp2.WSGIApplication([
  ('/', MainPage),
  ('/testdata', TestData),
], debug=True)

