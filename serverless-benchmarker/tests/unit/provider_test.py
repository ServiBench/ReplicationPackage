from sb.provider import Provider


def test_volume_mount_aws():
    p = Provider('aws')
    assert p.volume_mount() == 'aws-secrets:/root/.aws'
