# Collaboration

Real-time multiplayer editing and collaboration features in Zed.

## Overview

Zed includes built-in collaboration features:

- **Channels**: Persistent team spaces
- **Screen Sharing**: Share your editor view
- **Multiplayer Editing**: Real-time co-editing
- **Voice Chat**: Built-in audio communication

## Getting Started

### Sign In

Collaboration requires a Zed account:

1. Click the profile icon (bottom left)
2. Select "Sign In"
3. Authenticate with GitHub

### Requirements

- Zed account (free)
- Internet connection
- Participants need Zed installed

## Channels

Channels are persistent spaces for teams to collaborate.

### Create a Channel

1. Open Collaboration panel (++cmd+shift+c++)
2. Click "+" to create channel
3. Name your channel
4. Invite members

### Channel Structure

```
Organization
├── #general
├── #engineering
│   ├── #frontend
│   └── #backend
└── #design
```

### Channel Permissions

- **Admin**: Manage channel, invite members
- **Member**: Join calls, share projects
- **Guest**: View-only access

### Invite Members

1. Right-click channel
2. Select "Manage Members"
3. Search by GitHub username
4. Set permission level

## Sharing a Project

### Start Sharing

1. Open project in Zed
2. Click "Share" in title bar or
3. Command Palette > "call: share project"

### Share with Channel

1. Join a channel call
2. Share project automatically visible to participants
3. Click "Follow" to sync views

### Direct Sharing

1. Start a call with contact
2. Share project
3. Participant can request access

## Joining a Shared Project

### From Channel

1. Open Collaboration panel
2. Click active channel
3. See shared projects
4. Click to join or follow

### Accept Invite

When invited directly:

1. Notification appears
2. Click to accept
3. Project opens in new workspace

## Multiplayer Editing

### Following

Follow a collaborator to see their view:

1. Click their avatar in the title bar
2. Your view syncs with theirs
3. Click again or navigate to stop following

### Co-editing

- Multiple cursors visible in real-time
- Each participant has a unique color
- See who's editing what instantly

### Presence Indicators

| Indicator | Meaning |
|-----------|---------|
| Colored cursor | Active editing |
| Colored selection | Selected text |
| Avatar in tab | File being viewed |
| Line highlight | Current line |

## Voice Chat

### Start Voice Chat

In a channel:

1. Click microphone icon
2. Audio starts automatically

Or via Command Palette:

- "call: toggle mute"
- "call: toggle deafen"

### Audio Controls

| Key | Action |
|-----|--------|
| ++cmd+shift+m++ | Toggle mute |
| - | Toggle deafen (Command Palette) |

### Audio Settings

```json
{
  "calls": {
    "mute_on_join": true,
    "share_on_join": false
  }
}
```

## Screen Sharing

### Share Screen

1. During call, click screen share icon
2. Select screen or window
3. Participants see your screen

### Viewing Shared Screen

- Appears in collaboration panel
- Click to focus
- Works alongside code sharing

## Workflow Examples

### Pair Programming

1. Create/join channel
2. Share project
3. Partner follows you
4. Voice chat while coding
5. Take turns driving

### Code Review

1. Share project with reviewer
2. Navigate to changes
3. Reviewer follows and comments
4. Discuss via voice

### Team Planning

1. Create channel for team
2. Share architecture docs
3. Everyone views together
4. Discuss and edit collaboratively

## Settings

### Collaboration Settings

```json
{
  "calls": {
    "mute_on_join": true,
    "share_on_join": false
  },
  "collaboration_panel": {
    "dock": "left"
  }
}
```

### Notification Settings

Control collaboration notifications in system preferences or Zed settings.

## Privacy

### Project Sharing

- Only shared projects are visible
- Sharing can be revoked anytime
- File changes sync in real-time

### Audio Privacy

- Mute by default available
- Push-to-talk coming soon
- Audio is peer-to-peer when possible

## Keybindings

| Key | Action |
|-----|--------|
| ++cmd+shift+c++ | Toggle collaboration panel |
| ++cmd+shift+m++ | Toggle mute |
| - | Share project (via palette) |
| - | Follow participant (click avatar) |

## Troubleshooting

### Can't Connect to Channel

1. Check internet connection
2. Verify Zed account signed in
3. Check channel permissions
4. Restart Zed

### Audio Issues

1. Check system audio permissions
2. Verify microphone selected
3. Check mute status
4. Restart call

### Sync Lag

1. Check network stability
2. Large files may have delay
3. Close unused projects

## Best Practices

1. **Mute when not speaking**: Reduces background noise
2. **Use channels**: Organize by team/project
3. **Follow actively**: Stay synced during reviews
4. **Share specific projects**: Don't over-share
5. **Use voice**: Faster than typing for discussions
