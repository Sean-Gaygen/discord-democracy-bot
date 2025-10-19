from WebsiteHandler import WebsiteHandler

print("Unposted provisions:")

for provision in WebsiteHandler.get_unposted_provisions():

	print(provision)

print()
print("resolvable provisions:")

for provision in WebsiteHandler.get_resolvable_provisions():

	print(provision)

print()

open_provisions = WebsiteHandler.get_open_provisions()

print(f"Open resolutions {len(open_provisions)} in total:")

for provision in open_provisions:

	print(provision)

print()

print('basic inflation stats')

money_dict = WebsiteHandler.get_debug_inflation()

for name, value in money_dict.items():

	print(f'{name}, {value}')

print()
print('crack stats')

for name, value in WebsiteHandler.get_debug_inflation(WebsiteHandler.get_price_of_crack()).items():

	print(f'{name}, {value}')


print()
print("updatable positions")

for position in WebsiteHandler.get_updatable_temporary_positions():

	print(position)