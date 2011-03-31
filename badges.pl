use warnings;
use strict;

use Cairo;
use POSIX qw( ceil );
use List::Util qw( max min );

# All dimensions are inches.
use constant {
    PTS_IN_ONE_IN => 72,

    PAGE_WIDTH => 8.5,
    PAGE_HEIGHT => 11,
    PAGE_LEFT_MARGIN => 1,
    PAGE_RIGHT_MARGIN => 1,
    PAGE_TOP_MARGIN => 1,
    PAGE_BOTTOM_MARGIN => 1,
    BADGE_WIDTH => 2.75,
    BADGE_HEIGHT => 1.8,
    BADGE_LEFT_MARGIN => 0.1,
    BADGE_RIGHT_MARGIN => 0.1,
    BADGE_TOP_MARGIN => 0.1,
    BADGE_BOTTOM_MARGIN => 0.1,
    BADGE_H_SPACING => 0.5,
    BADGE_V_SPACING => 0.5,
    BADGE_WIDTH_PROPORTION => 0.25,

    TITLE => "Mayfest 2011",

    NAME_CENTER_OFFSET => -0.1,
    SPACING_BELOW_NAME => 0.2,
    NAME_RIGHT_NUDGE => 0,
    INSTITUTION_RIGHT_NUDGE => 0,

    TITLE_MAX_FONT_SIZE => 50,
    NAME_MAX_FONT_SIZE => 20,
    INSTITUTION_MAX_FONT_SIZE => 15,

    FONT_SIZE_EPSILON => 2,
};
use constant TITLE_COLOR => (182/255, 0, 0);
use constant NAME_COLOR => (0, 0, 0);
use constant INSTITUTION_COLOR => (0, 0, 0);
use constant TITLE_FONT => ("Verdana", "normal", "normal");
use constant NAME_FONT => ("Verdana", "normal", "normal");
use constant INSTITUTION_FONT => ("Verdana", "italic", "normal");

sub in_to_pt { return shift() * PTS_IN_ONE_IN }
sub in_to_pti { return int(shift() * PTS_IN_ONE_IN); }
sub pt_to_in { return shift() / PTS_IN_ONE_IN; }

my $surface = Cairo::PdfSurface->create("badges.pdf", in_to_pti(PAGE_WIDTH), in_to_pti(PAGE_HEIGHT));
my $cr = Cairo::Context->create($surface);
my $logo_surface = Cairo::ImageSurface->create_from_png("logo.png");

sub with_transform (&@) {
    my ($code, $cr, $transform) = @_;

    my $old_matrix = $cr->get_matrix();
    $cr->set_matrix($transform);
    &$code;
    $cr->set_matrix($old_matrix);
}
sub with_source (&@) {
    my ($code, $cr, $source) = @_;

    my $old_source = $cr->get_source();
    $cr->set_source($source);
    &$code;
    $cr->set_source($old_source);
}

sub get_best_font_size_ {
    my ($count, $upper, $lower, $size, $text, $maxw, $maxh, $epsilon) = @_;

    die "Recursion too deep" unless $count <= 50;

    $cr->set_font_size($size);
    my $e = $cr->text_extents($text);
    my $xdiff = $maxw - $e->{width};
    my $ydiff = $maxh - $e->{height};
#    print "S: $size, ", in_to_pt($size),
#          ", $xdiff, $ydiff\n";
    if ($xdiff >= 0 && $ydiff >= 0 && min($xdiff, $ydiff) <= $epsilon) {
        return $size;
    }
    elsif ($xdiff > 0 && $ydiff > 0) { # Too small.
        return $size if $size == $upper;
        get_best_font_size_($count+1 , $upper, $size, ($size + $upper)/2, $text, $maxw, $maxh, $epsilon);
    }
    else { # Too big.
        get_best_font_size_($count+1, $size, $lower, ($size + $lower)/2, $text, $maxw, $maxh, $epsilon);
    }
}
sub get_best_font_size {
    my $r = get_best_font_size_(0, $_[0], 0, @_);
    return $r;
}

sub draw_badge {
    my ($x, $y, $info) = @_;

    # Change origin to ($x, $y) and scale to inches instead of points.
    with_transform {
        # Draw bounding rectangle.
        $cr->rectangle(0, 0, BADGE_WIDTH, BADGE_HEIGHT);
        $cr->set_line_width(pt_to_in(0.5));
        $cr->stroke();

        # Draw UMD logo.
        my $logo_surface_pattern = Cairo::SurfacePattern->create($logo_surface);
        my $badge_width_in_pts = in_to_pt(BADGE_WIDTH);
        my $logo_portion_pts = BADGE_WIDTH_PROPORTION * $badge_width_in_pts;
        my $scale_factor = $logo_surface->get_width() / $logo_portion_pts;
        my $scale = in_to_pt($scale_factor);
        $logo_surface_pattern->set_matrix(Cairo::Matrix->init($scale, 0, 0, $scale, 0, 0));
        with_source {
            $logo_surface_pattern->set_filter('nearest');
            $logo_surface_pattern->set_extend('none');
            $cr->rectangle(0, 0, 200/72, 200/72);
            $cr->fill();
        } $cr, $logo_surface_pattern;

        # Draw title.
        $cr->select_font_face(TITLE_FONT);
        $cr->set_font_size(
            get_best_font_size(
                pt_to_in(TITLE_MAX_FONT_SIZE),
                TITLE,
                pt_to_in($badge_width_in_pts-$logo_portion_pts) - BADGE_RIGHT_MARGIN,
                BADGE_HEIGHT, # Doesn't matter what we give here since width is the real constraint.
                pt_to_in(FONT_SIZE_EPSILON)
            )
        );
        my $logo_vportion = pt_to_in($logo_surface->get_height() / $scale_factor);
        my $title_extents = $cr->text_extents(TITLE);
        $cr->move_to(pt_to_in($logo_portion_pts), -$title_extents->{y_bearing} + ($logo_vportion/2) - ($title_extents->{height}/2));
        $cr->text_path(TITLE);
        $cr->set_source_rgb(TITLE_COLOR);
        $cr->fill();

        # Draw person's name.
        $cr->select_font_face(NAME_FONT);
        $cr->set_font_size(
            get_best_font_size(
                pt_to_in(NAME_MAX_FONT_SIZE),
                $info->{name},
                BADGE_WIDTH - BADGE_LEFT_MARGIN - BADGE_RIGHT_MARGIN,
                BADGE_HEIGHT, # Doesn't matter what we give here since width is the real constraint.
                pt_to_in(FONT_SIZE_EPSILON)
            )
        );
        my $name_extents = $cr->text_extents($info->{name});
        my $name_y;
        $cr->move_to(BADGE_LEFT_MARGIN + NAME_RIGHT_NUDGE + ((BADGE_WIDTH - BADGE_LEFT_MARGIN - BADGE_RIGHT_MARGIN - $name_extents->{width}) / 2),
                     $name_y = NAME_CENTER_OFFSET + (BADGE_HEIGHT / 2) - $name_extents->{y_bearing});
        $cr->text_path($info->{name});
        $cr->set_source_rgb(NAME_COLOR);
        $cr->fill();

        # Draw instutition.
        $cr->select_font_face(INSTITUTION_FONT);
        $cr->set_font_size(
            get_best_font_size(
                pt_to_in(INSTITUTION_MAX_FONT_SIZE),
                $info->{aff},
                BADGE_WIDTH - BADGE_LEFT_MARGIN - BADGE_RIGHT_MARGIN,
                BADGE_HEIGHT, # Doesn't matter what we give here since width is the real constraint.
                pt_to_in(FONT_SIZE_EPSILON)
            )
        );
        my $inst_extents = $cr->text_extents($info->{aff});
        $cr->move_to(BADGE_LEFT_MARGIN + INSTITUTION_RIGHT_NUDGE + ((BADGE_WIDTH - BADGE_LEFT_MARGIN - BADGE_RIGHT_MARGIN - $inst_extents->{width}) / 2),
                     $name_y + SPACING_BELOW_NAME - $inst_extents->{y_bearing});
        $cr->text_path($info->{aff});
        $cr->set_source_rgb(INSTITUTION_COLOR);
        $cr->fill();
    } $cr, Cairo::Matrix->init(1, 0, 0, 1, $x + BADGE_LEFT_MARGIN, $y + BADGE_TOP_MARGIN)
           ->multiply(Cairo::Matrix->init(in_to_pt(1), 0, 0, in_to_pt(1), 1, 1));
}

sub draw_one_page_of_badges {
    my ($badges, $i) = @_;

    for (my $x = PAGE_LEFT_MARGIN;
         $x + BADGE_WIDTH <= PAGE_WIDTH - PAGE_RIGHT_MARGIN;
         $x += BADGE_WIDTH + BADGE_H_SPACING) {
        for (my $y = PAGE_TOP_MARGIN;
             $i < scalar(@$badges) && $y + BADGE_HEIGHT <= PAGE_HEIGHT - PAGE_BOTTOM_MARGIN;
             $y += BADGE_HEIGHT + BADGE_V_SPACING, ++$i) {
            draw_badge($x, $y, $badges->[$i]);
        }
    }

    return $i;
}

sub draw_badges {
    my $badges = shift;

    for (my $i = 0; $i < scalar(@$badges); $i = draw_one_page_of_badges($badges, $i)) {
        $cr->show_page() if $i > 0;
    }
}

# Parse 'registrations' file.
use constant REQUIRED_KEYS => qw( name aff email friday saturday reception crash ); # 'comments' not required.
open my $regs, "registrations" or die "Unable to open 'registrations' file.";
my $state = 'initial';
my @records;
my $current_record = { };
for my $line (<$regs>) {
    if ($state eq 'initial') {
        if ($line =~ /^\s*$/) {
            ;
        }
        elsif ($line =~ /^\s*--\s*$/) {
            $state = 'date';
        }
        else { die "Error parsing 'records'."; }
    }
    elsif ($state eq 'date') {
        if ($line !~ /^\s*(?:(?:Mon)|(?:Tue)|(?:Wed)|(?:Thu)|(?:Fri))\s+(?:(?:Jan)|(?:Feb)|(?:Mar)|(?:Apr)|(?:May)|(?:Jun)|(?:Jul)|(?:Aug)|(?:Sep)|(?:Oct)|(?:Nov)|(?:Dec))\s+\d{1,2} \d\d:\d\d:\d\d\s+\d\d\d\d\s*$/) {
            die "Bad date ('$line')";
        }
        else { $state = 'in_record'; }
    }
    elsif ($state eq 'in_record') {
        if ($line =~ /^\s*$/) {
            push @records, $current_record;
            $current_record = { };
            $state = 'initial';
        }
        elsif ($line =~ /^\s*([\w\s]+):\s*(.*)$/) {
            $current_record->{$1} = $2;
        }
        else {
            die "Error parsing 'records'.";
        }
    }
    else { die "Bad state."; }
}
push @records, $current_record if scalar(%$current_record);
foreach my $r (@records) {
    for my $k (REQUIRED_KEYS) {
        die "Required key missing ('$k')" unless $r->{$k};
    }
}

draw_badges(\@records);

# TEST
# draw_badges([
#     { name => "Brian Dillon",
#       institution => "University of Maryland"
#     },
#     { name => "Collin Phillips",
#       institution => "University of Maryland"
#     },
#     { name => "Sir Person Bearing a Very Long Name Indeed",
#       institution => "Prolixity Institute"
#     }
# ])
