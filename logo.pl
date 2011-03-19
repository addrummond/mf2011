use warnings;
use strict;

use Cairo;
use List::Util qw( max );
use POSIX qw( ceil );

sub rgb { return (shift() / 255, shift() / 255, shift() / 255); }

my @FONT = ($ARGV[0] || "Museo Sans", "normal", "normal");
my $FONT_SIZE = 60;

my @DARK = rgb(48,56,94);
my @LIGHT = rgb(110,121,174);
my @TOUTLINE = rgb(255, 255, 255);#@DARK;
my @DARK2 = rgb(138,100,60);
my @LIGHT2 = rgb(196,167,135);
my @TOUTLINE2 = rgb(255, 255, 255);#@DARK;

my @BACK = @LIGHT2;
my @LIGHTBACK = rgb(242,237,232);

my @TEXTPOS = (0, 0);

my $TEXT1 = uc "Mayfest";
my $TEXT2 = "2011";

my $XSPACE = 20;

my $GRADIENT_X_OFFSET = 0.333;
my $GRADIENT_X_OFFSET2 = 0.333;

my $OUTLINE_WIDTH = 2;

my @BORDER = (10, 10);

my $GAP = 1/5;

##########


my $surface = Cairo::ImageSurface->create('argb32', 50, 50);
my $cr = Cairo::Context->create($surface);
$cr->select_font_face(@FONT);
$cr->set_font_size($FONT_SIZE);
my $extents = $cr->text_extents($TEXT1);
my $x = $BORDER[0]/2 + $extents->{width} + $TEXTPOS[0] + $XSPACE;
my $extents2 = $cr->text_extents($TEXT2);

my $WIDTH = $x + $extents2->{width} + $BORDER[0];
my $HEIGHT = max($extents->{height}, $extents2->{height}) + $BORDER[1];
$surface = Cairo::ImageSurface->create('argb32', $WIDTH, $HEIGHT);
$cr = Cairo::Context->create($surface);
$cr->select_font_face(@FONT);
$cr->set_font_size($FONT_SIZE);

my $gap_px = $GAP*$HEIGHT;
$cr->set_source_rgb(@BACK);
$cr->rectangle(0, $gap_px, $WIDTH, $HEIGHT-($gap_px*2));
$cr->fill();
$cr->set_source_rgb(@LIGHTBACK);
$cr->rectangle(0, 0, $WIDTH, $gap_px);
$cr->fill();
$cr->set_source_rgb(@LIGHTBACK);
$cr->rectangle(0, $HEIGHT-$gap_px, $WIDTH, $HEIGHT);
$cr->fill();

print("DIMS: $WIDTH,$HEIGHT\n");
print("BAND HEIGHT: ", int(ceil($HEIGHT - (2*$gap_px))), "px\n");
print("BORDER HEIGHT: ", $gap_px, "px\n");

my $grad = Cairo::LinearGradient->create($BORDER[0]/2, $BORDER[1]/2, $BORDER[0]/2 + $extents->{width}, $BORDER[1]/2 + $extents->{height});
$grad->add_color_stop_rgb(0, @LIGHT);
$grad->add_color_stop_rgb($GRADIENT_X_OFFSET, @DARK);
$grad->add_color_stop_rgb(1.0, @LIGHT);
$cr->set_source($grad);
$cr->move_to($BORDER[0]/2, -$extents->{y_bearing} + $BORDER[1]/2);
$cr->text_path($TEXT1);
$cr->fill();
$cr->move_to($BORDER[0]/2, -$extents->{y_bearing} + $BORDER[1]/2);
$cr->text_path($TEXT1);
$cr->set_source_rgb(@TOUTLINE);
$cr->set_line_width($OUTLINE_WIDTH);
$cr->stroke();

$grad = Cairo::LinearGradient->create($x, $BORDER[1]/2, $x + $extents2->{width}, $BORDER[1]/2);
$grad->add_color_stop_rgb(0, @LIGHT2);
$grad->add_color_stop_rgb($GRADIENT_X_OFFSET2, @DARK2);
$grad->add_color_stop_rgb(1.0, @LIGHT2);
$cr->set_source($grad);
$cr->move_to($x, -$extents->{y_bearing} + $BORDER[1]/2);
$cr->text_path($TEXT2);
$cr->fill();
$cr->move_to($x, -$extents->{y_bearing} + $BORDER[1]/2);
$cr->text_path($TEXT2);
$cr->set_source_rgb(@TOUTLINE2);
$cr->set_line_width($OUTLINE_WIDTH);
$cr->stroke();

$surface->write_to_png('static/mf2011logo.png');
